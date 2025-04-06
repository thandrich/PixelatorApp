from app import app

if __name__ == "__main__":
    from import_palettes import main as import_palettes
    with app.app_context():
        import_palettes()
    app.run(host="0.0.0.0", port=5000, debug=True)