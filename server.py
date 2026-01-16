import http.server
import socketserver
import os
import json
import sys
from urllib.parse import unquote
import mimetypes

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
BIBLIOTECA_JSON = os.path.join(BASE_DIR, "biblioteca.json")

# Tipos de archivos permitidos
ALLOWED_EXTENSIONS = {
    # Documentos
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.txt': 'text/plain',
    '.rtf': 'application/rtf',
    '.odt': 'application/vnd.oasis.opendocument.text',
    
    # Hojas de cálculo
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
    '.csv': 'text/csv',
    
    # Presentaciones
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.odp': 'application/vnd.oasis.opendocument.presentation',
    
    # Imágenes
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
    
    # Archivos comprimidos
    '.zip': 'application/zip',
    '.rar': 'application/vnd.rar',
    '.7z': 'application/x-7z-compressed',
    '.tar': 'application/x-tar',
    '.gz': 'application/gzip',
    
    # Otros
    '.json': 'application/json',
    '.xml': 'application/xml',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.py': 'text/x-python',
    '.java': 'text/x-java-source',
    '.c': 'text/x-c',
    '.cpp': 'text/x-c++',
}

# Crear estructura de carpetas
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ------------------ Funciones ------------------
def cargar_metadata():
    if not os.path.exists(BIBLIOTECA_JSON):
        return []
    try:
        with open(BIBLIOTECA_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def guardar_metadata(data):
    with open(BIBLIOTECA_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def es_extension_permitida(filename):
    """Verifica si la extensión del archivo está permitida"""
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS

def obtener_tipo_mime(filename):
    """Obtiene el tipo MIME del archivo"""
    _, ext = os.path.splitext(filename.lower())
    return ALLOWED_EXTENSIONS.get(ext, 'application/octet-stream')

# ------------------ Handler ------------------
class FileHandler(http.server.SimpleHTTPRequestHandler):
    
    def _send_response(self, data, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, bytes):
            data = json.dumps(data).encode('utf-8')
        self.wfile.write(data)
    
    # GET: /files, /uploads/*, archivos estáticos
    def do_GET(self):
        try:
            if self.path == '/files' or self.path == '/pdfs':
                metadata = cargar_metadata()
                self._send_response(metadata)
                return
                
            elif self.path.startswith('/uploads/'):
                filename = unquote(self.path[9:])  # Quitar "/uploads/"
                if '..' in filename or '/' in filename:
                    self._send_response({'error': 'Ruta inválida'}, 400)
                    return
                    
                filepath = os.path.join(UPLOAD_DIR, filename)
                if os.path.exists(filepath):
                    # Determinar tipo MIME
                    mime_type = obtener_tipo_mime(filename)
                    
                    self.send_response(200)
                    self.send_header('Content-Type', mime_type)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Disposition', f'inline; filename="{filename}"')
                    self.end_headers()
                    
                    with open(filepath, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    self._send_response({'error': 'Archivo no encontrado'}, 404)
                return
                
            else:
                # Servir archivos estáticos (HTML, CSS, JS)
                if self.path == '/':
                    self.path = '/index.html'
                
                # Permitir solo archivos dentro del directorio base
                filepath = os.path.join(BASE_DIR, self.path.lstrip('/'))
                if not os.path.exists(filepath) or not filepath.startswith(BASE_DIR):
                    self._send_response({'error': 'Archivo no encontrado'}, 404)
                    return
                
                # Determinar tipo de contenido usando mimetypes
                mime_type, _ = mimetypes.guess_type(filepath)
                if not mime_type:
                    mime_type = 'text/plain'
                
                self.send_response(200)
                self.send_header('Content-Type', mime_type)
                self.end_headers()
                
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
                    
        except Exception as e:
            print(f"Error en GET: {e}", file=sys.stderr)
            self._send_response({'error': str(e)}, 500)
    
    # POST: /upload
    def do_POST(self):
        if self.path == '/upload':
            try:
                content_type = self.headers.get('Content-Type', '')
                
                if 'multipart/form-data' not in content_type:
                    self._send_response({'error': 'Formato inválido'}, 400)
                    return
                
                # Leer todo el contenido
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self._send_response({'error': 'No se recibió archivo'}, 400)
                    return
                
                post_data = self.rfile.read(content_length)
                
                # Parsear multipart manualmente
                boundary = None
                for part in content_type.split(';'):
                    part = part.strip()
                    if part.startswith('boundary='):
                        boundary = '--' + part[9:]
                        break
                
                if not boundary:
                    self._send_response({'error': 'Boundary no encontrado'}, 400)
                    return
                
                # Dividir por boundary
                parts = post_data.split(boundary.encode())
                filename = None
                file_data = None
                
                for part in parts:
                    if b'filename="' in part:
                        # Extraer nombre
                        start = part.find(b'filename="') + 10
                        end = part.find(b'"', start)
                        filename = part[start:end].decode('utf-8')
                        
                        # Extraer datos
                        header_end = part.find(b'\r\n\r\n')
                        if header_end != -1:
                            file_data = part[header_end+4:]
                            # Limpiar CRLF final
                            if file_data.endswith(b'\r\n'):
                                file_data = file_data[:-2]
                            break
                
                if not filename or not file_data:
                    self._send_response({'error': 'No se encontró archivo'}, 400)
                    return
                
                # Verificar extensión permitida
                if not es_extension_permitida(filename):
                    extensiones_permitidas = ', '.join(ALLOWED_EXTENSIONS.keys())
                    self._send_response({
                        'error': f'Tipo de archivo no permitido',
                        'detalle': f'Extensiones permitidas: {extensiones_permitidas}'
                    }, 400)
                    return
                
                # Evitar duplicados
                base_name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(UPLOAD_DIR, filename)):
                    filename = f"{base_name}_{counter}{ext}"
                    counter += 1
                
                # Guardar archivo
                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(file_data)
                
                # Obtener tipo de archivo
                tipo_archivo = 'documento'
                _, ext = os.path.splitext(filename.lower())
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']:
                    tipo_archivo = 'imagen'
                elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                    tipo_archivo = 'comprimido'
                elif ext in ['.xls', '.xlsx', '.ods', '.csv']:
                    tipo_archivo = 'hoja_calculo'
                elif ext in ['.ppt', '.pptx', '.odp']:
                    tipo_archivo = 'presentacion'
                
                # Actualizar metadata
                metadata = cargar_metadata()
                metadata.append({
                    'nombre': filename,
                    'tipo': tipo_archivo,
                    'extension': ext,
                    'categoria': 'Sin categoría',
                    'scroll': 0,
                    'tamaño': len(file_data),
                    'fecha': os.path.getctime(filepath),
                    'mime_type': obtener_tipo_mime(filename)
                })
                guardar_metadata(metadata)
                
                self._send_response({
                    'mensaje': 'Archivo subido correctamente',
                    'nombre': filename,
                    'tipo': tipo_archivo,
                    'tamaño': len(file_data)
                })
                
            except Exception as e:
                print(f"Error en POST: {e}", file=sys.stderr)
                self._send_response({'error': str(e)}, 500)
            return
        
        self._send_response({'error': 'Ruta no encontrada'}, 404)
    
    # DELETE: /uploads/filename
    def do_DELETE(self):
        if self.path.startswith('/uploads/'):
            try:
                filename = unquote(self.path[9:])
                if '..' in filename or '/' in filename:
                    self._send_response({'error': 'Ruta inválida'}, 400)
                    return
                
                filepath = os.path.join(UPLOAD_DIR, filename)
                if not os.path.exists(filepath):
                    self._send_response({'error': 'Archivo no encontrado'}, 404)
                    return
                
                # Eliminar archivo
                os.remove(filepath)
                
                # Actualizar metadata
                metadata = cargar_metadata()
                metadata = [m for m in metadata if m['nombre'] != filename]
                guardar_metadata(metadata)
                
                self._send_response({'mensaje': 'Archivo eliminado'})
                
            except Exception as e:
                print(f"Error en DELETE: {e}", file=sys.stderr)
                self._send_response({'error': str(e)}, 500)
            return
        
        self._send_response({'error': 'Ruta no encontrada'}, 404)
    
    # PUT: /update
    def do_PUT(self):
        if self.path == '/update':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self._send_response({'error': 'Cuerpo vacío'}, 400)
                    return
                
                data = json.loads(self.rfile.read(content_length).decode('utf-8'))
                
                if 'nombre' not in data:
                    self._send_response({'error': 'Falta nombre'}, 400)
                    return
                
                metadata = cargar_metadata()
                encontrado = False
                
                for item in metadata:
                    if item['nombre'] == data['nombre']:
                        if 'scroll' in data:
                            item['scroll'] = int(data['scroll'])
                        if 'categoria' in data:
                            item['categoria'] = data['categoria']
                        encontrado = True
                        break
                
                if encontrado:
                    guardar_metadata(metadata)
                    self._send_response({'mensaje': 'Actualizado'})
                else:
                    self._send_response({'error': 'Archivo no encontrado'}, 404)
                    
            except json.JSONDecodeError:
                self._send_response({'error': 'JSON inválido'}, 400)
            except Exception as e:
                print(f"Error en PUT: {e}", file=sys.stderr)
                self._send_response({'error': str(e)}, 500)
            return
        
        self._send_response({'error': 'Ruta no encontrada'}, 404)
    
    # OPTIONS para CORS
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}", file=sys.stderr)

# ------------------ Inicio ------------------
if __name__ == '__main__':
    # Inicializar mimetypes
    mimetypes.init()
    
    # Inicializar metadata si no existe
    if not os.path.exists(BIBLIOTECA_JSON):
        guardar_metadata([])
    
    print("=" * 50)
    print("📁 GESTOR DE ARCHIVOS - SERVIDOR")
    print("=" * 50)
    print(f"📍 URL: http://localhost:{PORT}")
    print(f"📁 Uploads: {UPLOAD_DIR}")
    print("=" * 50)
    print("📄 Tipos de archivos permitidos:")
    for ext in sorted(ALLOWED_EXTENSIONS.keys()):
        print(f"   • {ext}")
    print("=" * 50)
    print("⚠️  SIN LÍMITE DE TAMAÑO para archivos subidos")
    print("⚠️  SOLO esta URL: http://localhost:8000")
    print("=" * 50)
    
    with socketserver.TCPServer(('', PORT), FileHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Servidor detenido")