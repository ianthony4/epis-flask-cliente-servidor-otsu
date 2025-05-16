from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import os

app = Flask(__name__)
PROCESSED_FOLDER = os.path.join(app.static_folder, 'processed')
UPLOAD_FOLDER = os.path.join(app.static_folder, '')
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route("/")
def index():
    image_folder = os.path.join(app.static_folder)
    images = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    return render_template("index.html", images=images)

@app.route("/processed")
def processed():
    processed_folder = os.path.join(app.static_folder, "processed")
    images = [f for f in os.listdir(processed_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    return render_template("processed.html", images=images)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if 'image' not in request.files:
            return "No se subió ninguna imagen", 400
        file = request.files['image']
        if file.filename == '':
            return "Nombre de archivo vacío", 400
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        try:
            file.save(filepath)
        except Exception as e:
            return f"Error al guardar: {e}", 500
        return "Imagen recibida", 200
    return render_template('upload.html')


# NUEVA RUTA PARA PROCESAR IMÁGENES DESDE LA WEB
@app.route("/process_image/<image_name>", methods=["POST"])
def process_image(image_name):
    import cv2

    image_path = os.path.join(app.static_folder, image_name)
    if not os.path.exists(image_path):
        return "Imagen no encontrada", 404

    # Leer imagen en color
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        return "No se pudo leer la imagen", 400

    # Convertir a escala de grises suave (no Otsu)
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    processed_name = f"gray_{image_name}"
    processed_path = os.path.join(app.static_folder, "processed", processed_name)
    cv2.imwrite(processed_path, gray_img)

    return render_template(
        "process_success.html",
        original_name=image_name,
        processed_name=processed_name
    )


@app.route("/process_gray/<image_name>")
def process_gray(image_name):
    import cv2
    import io
    image_path = os.path.join(app.static_folder, image_name)
    if not os.path.exists(image_path):
        return "Imagen no encontrada", 404

    # Leer en color
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        return "No se pudo leer la imagen", 400

    # Convertir a escala de grises (suave)
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Codificar en memoria para enviar como archivo
    _, buffer = cv2.imencode('.png', gray_img)
    return send_file(
        io.BytesIO(buffer),
        mimetype='image/png',
        as_attachment=False,
        download_name=f"gray_{image_name}"
    )

@app.route("/list_images")
def list_images():
    image_folder = os.path.join(app.static_folder)
    images = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    return jsonify(images)

@app.route("/upload_processed", methods=["POST"])
def upload_processed():
    processed_folder = os.path.join(app.static_folder, "processed")
    if 'image' not in request.files:
        return "No se subió ninguna imagen", 400
    file = request.files['image']
    if file.filename == '':
        return "Nombre de archivo vacío", 400
    filepath = os.path.join(processed_folder, file.filename)
    file.save(filepath)
    return f"Imagen procesada recibida y guardada como: {file.filename}", 200


if __name__ == "__main__":
    app.run(debug=True)
