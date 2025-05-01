document.addEventListener('DOMContentLoaded', function() {
    const recordBtn = document.getElementById('recordButton');
    const translateBtn = document.getElementById('translateBtn');
    const speakBtn = document.getElementById('speakBtn');
    const swapBtn = document.getElementById('swapLanguages');
    const inputText = document.getElementById('inputText');
    const outputText = document.getElementById('outputText');
    const sourceLanguage = document.getElementById('sourceLanguage');
    const targetLanguage = document.getElementById('targetLanguage');
    
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    // Swap languages
    swapBtn.addEventListener('click', function() {
        const temp = sourceLanguage.value;
        sourceLanguage.value = targetLanguage.value;
        targetLanguage.value = temp;
    });

    // Record voice
    recordBtn.addEventListener('click', async function() {
        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();
                isRecording = true;
                recordBtn.innerHTML = '<i class="bi bi-stop-circle"></i>';
                audioChunks = [];
                
                mediaRecorder.ondataavailable = function(e) {
                    audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = async function() {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    await sendAudioToServer(audioBlob);
                };
                
            } catch (err) {
                console.error('Error accessing microphone:', err);
                alert('Microphone access denied. Please allow microphone permission.');
            }
        } else {
            mediaRecorder.stop();
            isRecording = false;
            recordBtn.innerHTML = '<i class="bi bi-mic"></i>';
        }
    });

    // Translate text
    translateBtn.addEventListener('click', function() {
        const text = inputText.value.trim();
        if (!text) {
            alert('Please enter text to translate');
            return;
        }
        
        translateText(text);
    });

    // Speak translation
    speakBtn.addEventListener('click', function() {
        const translatedText = outputText.textContent;
        if (translatedText) {
            speakText(translatedText, targetLanguage.value);
        }
    });

    async function translateText(text) {
        try {
            const response = await fetch('/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    src_lang: sourceLanguage.value,
                    tgt_lang: targetLanguage.value
                })
            });
            
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            
            outputText.textContent = data.translated;
            speakBtn.disabled = false;
            
        } catch (error) {
            console.error('Translation error:', error);
            outputText.textContent = 'Error: ' + error.message;
        }
    }

    async function sendAudioToServer(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            formData.append('src_lang', sourceLanguage.value);
            
            const response = await fetch('/transcribe', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            
            inputText.value = data.text;
            translateText(data.text);
            
        } catch (error) {
            console.error('Audio processing error:', error);
            outputText.textContent = 'Error processing audio: ' + error.message;
        }
    }

    function speakText(text, lang) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang;
        window.speechSynthesis.speak(utterance);
    }
});