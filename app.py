from app import app

# Alternatively, you can run via:
# flask run --debug
# ie. using the CLI tool.

if __name__ == '__main__':
    app.run(debug=True, port=8080)
