from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,          # Keeps debug features
        use_reloader=False,  # Prevents dependency reinstallation
        use_debugger=True    # Maintains debug toolbar
    )