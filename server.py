import http.server
import socketserver
import os
import json
import sys
from urllib.parse import unquote
import mimetypes
import subprocess
import shutil
import tarfile
import xml.etree.ElementTree as ET
from datetime import datetime

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
    
    # Imágenes de disco (NUEVO)
    '.iso': 'application/x-iso9660-image',
    '.img': 'application/x-raw-disk-image',
    '.dmg': 'application/x-apple-diskimage',
    '.bin': 'application/octet-stream',
    '.nrg': 'application/x-nrg',
    
    # Máquinas virtuales (NUEVO)
    '.ova': 'application/x-virtualbox-ova',
    '.ovf': 'application/x-virtualbox-ovf',
    '.vbox': 'application/x-virtualbox-vbox',
    '.vdi': 'application/x-virtualbox-vdi',
    '.vhd': 'application/x-virtualbox-vhd',
    '.vhdx': 'application/x-virtualbox-vhdx',
    '.vmx': 'application/x-vmware-vmx',
    
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

# Tamaños máximos por tipo de archivo (en bytes)
MAX_FILE_SIZES = {
    'default': 100 * 1024 * 1024,  # 100 MB por defecto
    '.iso': 10 * 1024 * 1024 * 1024,  # 10 GB para ISOs
    '.img': 10 * 1024 * 1024 * 1024,  # 10 GB para IMG
    '.dmg': 10 * 1024 * 1024 * 1024,  # 10 GB para DMG
    '.ova': 10 * 1024 * 1024 * 1024,  # 10 GB para OVAs
    '.ovf': 10 * 1024 * 1024 * 1024,  # 10 GB para OVFs
    '.vdi': 20 * 1024 * 1024 * 1024,  # 20 GB para VDI
    '.vhd': 20 * 1024 * 1024 * 1024,  # 20 GB para VHD
    '.vhdx': 20 * 1024 * 1024 * 1024,  # 20 GB para VHDX
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

def obtener_tipo_archivo(extension):
    """Determina el tipo de archivo para la categorización"""
    extension = extension.lower()
    
    tipo_mapping = {
        # Documentos
        '.pdf': 'documento',
        '.doc': 'documento', '.docx': 'documento', '.txt': 'documento', '.rtf': 'documento', '.odt': 'documento',
        
        # Hojas de cálculo
        '.xls': 'hoja_calculo', '.xlsx': 'hoja_calculo', '.ods': 'hoja_calculo', '.csv': 'hoja_calculo',
        
        # Presentaciones
        '.ppt': 'presentacion', '.pptx': 'presentacion', '.odp': 'presentacion',
        
        # Imágenes
        '.jpg': 'imagen', '.jpeg': 'imagen', '.png': 'imagen', '.gif': 'imagen', '.bmp': 'imagen', '.svg': 'imagen', '.webp': 'imagen',
        
        # Archivos comprimidos
        '.zip': 'comprimido', '.rar': 'comprimido', '.7z': 'comprimido', '.tar': 'comprimido', '.gz': 'comprimido',
        
        # Imágenes de disco (NUEVO)
        '.iso': 'imagen_disco',
        '.img': 'imagen_disco',
        '.dmg': 'imagen_disco',
        '.bin': 'imagen_disco',
        '.nrg': 'imagen_disco',
        
        # Máquinas virtuales (NUEVO)
        '.ova': 'maquina_virtual',
        '.ovf': 'maquina_virtual',
        '.vbox': 'maquina_virtual',
        '.vdi': 'disco_virtual',
        '.vhd': 'disco_virtual',
        '.vhdx': 'disco_virtual',
        '.vmx': 'maquina_virtual',
        
        # Otros documentos
        '.json': 'documento',
        '.xml': 'documento',
        '.html': 'documento',
        '.htm': 'documento',
        '.js': 'documento',
        '.css': 'documento',
        '.py': 'documento',
        '.java': 'documento',
        '.c': 'documento',
        '.cpp': 'documento'
    }
    
    return tipo_mapping.get(extension, 'documento')

def obtener_metadata_archivo(filepath, filename, file_size):
    """Obtiene metadatos específicos según el tipo de archivo"""
    _, ext = os.path.splitext(filename.lower())
    metadata = {
        'size': file_size,
        'upload_date': datetime.now().isoformat()
    }
    
    try:
        # Para imágenes de disco (ISO/IMG/DMG)
        if ext in ['.iso', '.img', '.dmg', '.bin', '.nrg']:
            metadata.update(analizar_imagen_disco(filepath))
        
        # Para máquinas virtuales (OVA/OVF)
        elif ext in ['.ova', '.ovf']:
            metadata.update(analizar_maquina_virtual(filepath))
        
        # Para discos virtuales (VDI/VHD/VHDX)
        elif ext in ['.vdi', '.vhd', '.vhdx']:
            metadata.update(analizar_disco_virtual(filepath))
            
    except Exception as e:
        print(f"Error analizando metadatos de {filename}: {e}")
        metadata['analysis_error'] = str(e)
    
    return metadata

def analizar_imagen_disco(filepath):
    """Analiza una imagen de disco (ISO/IMG/DMG)"""
    metadata = {
        'type': 'disk_image',
        'bootable': False,
        'file_system': 'unknown',
        'architecture': 'unknown'
    }
    
    try:
        # Usar file command para obtener información básica
        if shutil.which('file'):
            result = subprocess.run(['file', filepath], capture_output=True, text=True)
            if result.returncode == 0:
                file_info = result.stdout.lower()
                
                # Detectar sistema operativo
                if 'windows' in file_info:
                    metadata['os_type'] = 'Windows'
                    metadata['architecture'] = 'x86/x64'
                elif 'linux' in file_info:
                    metadata['os_type'] = 'Linux'
                elif 'mac' in file_info or 'darwin' in file_info:
                    metadata['os_type'] = 'macOS'
                
                # Detectar si es booteable
                if 'boot' in file_info or 'bootable' in file_info:
                    metadata['bootable'] = True
                
                # Detectar sistema de archivos
                if 'iso9660' in file_info:
                    metadata['file_system'] = 'ISO9660'
                elif 'udf' in file_info:
                    metadata['file_system'] = 'UDF'
                elif 'fat' in file_info:
                    metadata['file_system'] = 'FAT'
                elif 'ntfs' in file_info:
                    metadata['file_system'] = 'NTFS'
                elif 'ext' in file_info:
                    metadata['file_system'] = 'ext'
        
        # Para ISOs, intentar obtener más información
        if filepath.lower().endswith('.iso'):
            metadata['iso_type'] = 'CD/DVD Image'
            metadata['standard'] = 'ISO9660/UDF'
            
    except Exception as e:
        print(f"Error analizando imagen de disco: {e}")
    
    return metadata

def analizar_maquina_virtual(filepath):
    """Analiza una máquina virtual (OVA/OVF)"""
    metadata = {
        'type': 'virtual_machine',
        'hypervisor': 'VirtualBox/VMware compatible'
    }
    
    try:
        if filepath.lower().endswith('.ova'):
            # Un OVA es un archivo TAR
            metadata['format'] = 'OVA (Open Virtualization Format Archive)'
            
            try:
                with tarfile.open(filepath, 'r') as tar:
                    # Buscar archivo OVF dentro del OVA
                    ovf_files = [member for member in tar.getmembers() 
                               if member.name.lower().endswith('.ovf')]
                    
                    if ovf_files:
                        # Extraer el primer OVF temporalmente
                        ovf_file = ovf_files[0]
                        temp_dir = '/tmp/vm_analysis'
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        tar.extract(ovf_file, path=temp_dir)
                        ovf_path = os.path.join(temp_dir, ovf_file.name)
                        
                        # Analizar OVF
                        ovf_metadata = analizar_ovf(ovf_path)
                        metadata.update(ovf_metadata)
                        
                        # Limpiar
                        try:
                            shutil.rmtree(temp_dir)
                        except:
                            pass
            except:
                pass
                
        elif filepath.lower().endswith('.ovf'):
            metadata['format'] = 'OVF (Open Virtualization Format)'
            ovf_metadata = analizar_ovf(filepath)
            metadata.update(ovf_metadata)
            
    except Exception as e:
        print(f"Error analizando máquina virtual: {e}")
    
    return metadata

def analizar_ovf(ovf_path):
    """Analiza un archivo OVF"""
    metadata = {}
    
    try:
        with open(ovf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Limpiar namespaces para facilitar el parsing
        import re
        content_clean = re.sub(r'xmlns="[^"]+"', '', content)
        
        try:
            root = ET.fromstring(content_clean)
            
            # Información básica
            name_elem = root.find('.//Name')
            if name_elem is not None and name_elem.text:
                metadata['vm_name'] = name_elem.text
            
            # Sistema operativo
            os_elem = root.find('.//OperatingSystemSection')
            if os_elem is not None:
                os_type = os_elem.get('{http://schemas.dmtf.org/ovf/envelope/1}id', '')
                if os_type:
                    metadata['os_type'] = os_type
            
            # Hardware
            virtual_system = root.find('.//VirtualSystem')
            if virtual_system is not None:
                system_type = virtual_system.get('{http://schemas.dmtf.org/ovf/envelope/1}id', '')
                if system_type:
                    metadata['system_type'] = system_type
            
            # Memoria
            import xml.etree.ElementTree as ET
            namespaces = {'rasd': 'http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData'}
            
            for elem in root.findall('.//'):
                if 'Memory' in elem.tag or 'RAM' in elem.tag:
                    for child in elem:
                        if 'VirtualQuantity' in child.tag:
                            try:
                                memory_mb = int(child.text) // 1024
                                metadata['memory_mb'] = memory_mb
                            except:
                                pass
            
            # Discos
            disk_elements = root.findall('.//rasd:HostResource', namespaces=namespaces)
            if disk_elements:
                metadata['disks'] = len(disk_elements)
            
            # Redes
            network_elements = root.findall('.//NetworkSection/Network')
            if network_elements:
                metadata['networks'] = len(network_elements)
                
        except ET.ParseError:
            # Intentar extraer información de forma básica
            if 'VirtualBox' in content:
                metadata['created_with'] = 'VirtualBox'
            elif 'VMware' in content:
                metadata['created_with'] = 'VMware'
    
    except Exception as e:
        print(f"Error analizando OVF: {e}")
    
    return metadata

def analizar_disco_virtual(filepath):
    """Analiza un disco virtual (VDI/VHD/VHDX)"""
    metadata = {
        'type': 'virtual_disk',
        'usage': 'Virtual machine storage'
    }
    
    try:
        # Determinar formato basado en extensión
        if filepath.lower().endswith('.vdi'):
            metadata['format'] = 'VDI (VirtualBox Disk Image)'
            metadata['compatible_with'] = 'VirtualBox'
        elif filepath.lower().endswith('.vhd'):
            metadata['format'] = 'VHD (Virtual Hard Disk)'
            metadata['compatible_with'] = 'VirtualBox, Hyper-V, VMware'
        elif filepath.lower().endswith('.vhdx'):
            metadata['format'] = 'VHDX (Virtual Hard Disk v2)'
            metadata['compatible_with'] = 'Hyper-V, VirtualBox 6+'
    
    except Exception as e:
        print(f"Error analizando disco virtual: {e}")
    
    return metadata

def obtener_hash_archivo(filepath):
    """Calcula el hash SHA256 de un archivo"""
    try:
        import hashlib
        sha256_hash = hashlib.sha256()
        
        with open(filepath, 'rb') as f:
            # Leer en bloques para archivos grandes
            for byte_block in iter(lambda: f.read(4096), b''):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    except:
        return None

# ------------------ Handler ------------------
class FileHandler(http.server.SimpleHTTPRequestHandler):
    
    def _send_response(self, data, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, bytes):
            data = json.dumps(data).encode('utf-8')
        self.wfile.write(data)
    
    # GET: /files, /uploads/*, /file-info/*, archivos estáticos
    def do_GET(self):
        try:
            # Listar archivos
            if self.path == '/files':
                metadata = cargar_metadata()
                
                # Añadir información adicional para cada archivo
                for item in metadata:
                    filepath = os.path.join(UPLOAD_DIR, item['nombre'])
                    if os.path.exists(filepath):
                        # Añadir tamaño real
                        item['tamaño_real'] = os.path.getsize(filepath)
                        
                        # Añadir tipo basado en extensión si no existe
                        if 'tipo' not in item:
                            _, ext = os.path.splitext(item['nombre'].lower())
                            item['tipo'] = obtener_tipo_archivo(ext)
                
                self._send_response(metadata)
                return
            
            # Información detallada de un archivo
            elif self.path.startswith('/file-info/'):
                filename = unquote(self.path[11:])
                if '..' in filename or '/' in filename:
                    self._send_response({'error': 'Ruta inválida'}, 400)
                    return
                
                filepath = os.path.join(UPLOAD_DIR, filename)
                if not os.path.exists(filepath):
                    self._send_response({'error': 'Archivo no encontrado'}, 404)
                    return
                
                # Obtener metadatos del archivo
                file_size = os.path.getsize(filepath)
                _, ext = os.path.splitext(filename.lower())
                
                metadata = {
                    'filename': filename,
                    'size': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'size_gb': round(file_size / (1024 * 1024 * 1024), 2),
                    'extension': ext,
                    'type': obtener_tipo_archivo(ext),
                    'upload_date': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                    'hash_sha256': obtener_hash_archivo(filepath)
                }
                
                # Añadir metadatos específicos según tipo
                specific_metadata = obtener_metadata_archivo(filepath, filename, file_size)
                metadata.update(specific_metadata)
                
                self._send_response(metadata)
                return
                
            # Descargar archivo
            elif self.path.startswith('/uploads/'):
                filename = unquote(self.path[9:])
                if '..' in filename or '/' in filename:
                    self._send_response({'error': 'Ruta inválida'}, 400)
                    return
                    
                filepath = os.path.join(UPLOAD_DIR, filename)
                if not os.path.exists(filepath):
                    self._send_response({'error': 'Archivo no encontrado'}, 404)
                    return
                
                # Determinar tipo MIME
                mime_type = obtener_tipo_mime(filename)
                
                # Para archivos grandes, usar streaming
                file_size = os.path.getsize(filepath)
                
                self.send_response(200)
                self.send_header('Content-Type', mime_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_header('Content-Length', str(file_size))
                
                # Cache headers para archivos grandes
                if file_size > 100 * 1024 * 1024:  # > 100MB
                    self.send_header('Cache-Control', 'public, max-age=3600')
                
                self.end_headers()
                
                # Enviar archivo en chunks
                with open(filepath, 'rb') as f:
                    chunk_size = 8192
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
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
                
                # Verificar tamaño máximo general
                MAX_UPLOAD_SIZE = 20 * 1024 * 1024 * 1024  # 20GB máximo general
                if content_length > MAX_UPLOAD_SIZE:
                    max_gb = MAX_UPLOAD_SIZE / (1024 * 1024 * 1024)
                    self._send_response({
                        'error': f'Archivo demasiado grande',
                        'detalle': f'Máximo permitido: {max_gb:.1f} GB'
                    }, 400)
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
                    extensiones_permitidas = ', '.join(sorted(ALLOWED_EXTENSIONS.keys()))
                    self._send_response({
                        'error': f'Tipo de archivo no permitido',
                        'detalle': f'Extensiones permitidas: {extensiones_permitidas}'
                    }, 400)
                    return
                
                # Verificar tamaño según tipo de archivo
                _, ext = os.path.splitext(filename.lower())
                max_size = MAX_FILE_SIZES.get(ext, MAX_FILE_SIZES['default'])
                
                if len(file_data) > max_size:
                    max_mb = max_size / (1024 * 1024)
                    if max_size > 1024 * 1024 * 1024:
                        max_gb = max_size / (1024 * 1024 * 1024)
                        self._send_response({
                            'error': f'Archivo demasiado grande para tipo {ext}',
                            'detalle': f'Máximo permitido: {max_gb:.1f} GB'
                        }, 400)
                    else:
                        self._send_response({
                            'error': f'Archivo demasiado grande para tipo {ext}',
                            'detalle': f'Máximo permitido: {max_mb:.0f} MB'
                        }, 400)
                    return
                
                # Evitar duplicados
                base_name, ext = os.path.splitext(filename)
                counter = 1
                original_filename = filename
                while os.path.exists(os.path.join(UPLOAD_DIR, filename)):
                    filename = f"{base_name}_{counter}{ext}"
                    counter += 1
                
                if original_filename != filename:
                    print(f"⚠️  Archivo renombrado: {original_filename} → {filename}")
                
                # Guardar archivo
                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(file_data)
                
                # Obtener tipo de archivo para categorización
                tipo_archivo = obtener_tipo_archivo(ext)
                
                # Obtener metadatos adicionales
                file_size = len(file_data)
                metadata_adicional = obtener_metadata_archivo(filepath, filename, file_size)
                
                # Calcular hash del archivo
                file_hash = obtener_hash_archivo(filepath)
                
                # Actualizar metadata
                metadata = cargar_metadata()
                file_metadata = {
                    'nombre': filename,
                    'tipo': tipo_archivo,
                    'extension': ext,
                    'categoria': 'Sin categoría',
                    'scroll': 0,
                    'tamaño': file_size,
                    'tamaño_mb': round(file_size / (1024 * 1024), 2),
                    'tamaño_gb': round(file_size / (1024 * 1024 * 1024), 2),
                    'fecha': datetime.now().isoformat(),
                    'fecha_timestamp': datetime.now().timestamp(),
                    'mime_type': obtener_tipo_mime(filename),
                    'hash_sha256': file_hash
                }
                
                # Añadir metadatos específicos
                file_metadata.update(metadata_adicional)
                metadata.append(file_metadata)
                guardar_metadata(metadata)
                
                # Respuesta con información completa
                response_data = {
                    'mensaje': 'Archivo subido correctamente',
                    'nombre': filename,
                    'nombre_original': original_filename,
                    'tipo': tipo_archivo,
                    'tamaño': file_size,
                    'tamaño_mb': round(file_size / (1024 * 1024), 2),
                    'tamaño_gb': round(file_size / (1024 * 1024 * 1024), 2),
                    'metadata': metadata_adicional
                }
                
                if original_filename != filename:
                    response_data['renombrado'] = True
                    response_data['nombre_original'] = original_filename
                
                self._send_response(response_data)
                
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
                initial_count = len(metadata)
                metadata = [m for m in metadata if m['nombre'] != filename]
                guardar_metadata(metadata)
                
                response = {
                    'mensaje': 'Archivo eliminado',
                    'archivo': filename,
                    'eliminado': True,
                    'metadata_actualizada': len(metadata) < initial_count
                }
                
                self._send_response(response)
                
            except Exception as e:
                print(f"Error en DELETE: {e}", file=sys.stderr)
                self._send_response({'error': str(e)}, 500)
            return
        
        self._send_response({'error': 'Ruta no encontrada'}, 404)
    
    # PUT: /update (para actualizar metadatos)
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
                        # Actualizar campos permitidos
                        campos_permitidos = ['scroll', 'categoria', 'tags', 'descripcion']
                        for campo in campos_permitidos:
                            if campo in data:
                                item[campo] = data[campo]
                        
                        # Actualizar fecha de modificación
                        item['ultima_modificacion'] = datetime.now().isoformat()
                        
                        encontrado = True
                        break
                
                if encontrado:
                    guardar_metadata(metadata)
                    self._send_response({
                        'mensaje': 'Actualizado',
                        'archivo': data['nombre'],
                        'actualizado': True
                    })
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
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Requested-With')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def log_message(self, format, *args):
        # Log simplificado para no saturar la consola
        message = format % args
        if '404' not in message:  # No loguear errores 404
            print(f"{self.address_string()} - {message}", file=sys.stderr)

# ------------------ Inicio ------------------
if __name__ == '__main__':
    # Inicializar mimetypes
    mimetypes.init()
    
    # Inicializar metadata si no existe
    if not os.path.exists(BIBLIOTECA_JSON):
        guardar_metadata([])
    
    print("=" * 60)
    print("🖥️  GESTOR DE ARCHIVOS - SERVIDOR")
    print("=" * 60)
    print(f"📍 URL: http://localhost:{PORT}")
    print(f"📁 Uploads: {UPLOAD_DIR}")
    print("=" * 60)
    print("📄 Tipos de archivos permitidos:")
    
    # Agrupar por categorías
    categorias = {
        'Documentos': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
        'Hojas de cálculo': ['.xls', '.xlsx', '.ods', '.csv'],
        'Presentaciones': ['.ppt', '.pptx', '.odp'],
        'Imágenes': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
        'Comprimidos': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        'Imágenes de disco': ['.iso', '.img', '.dmg', '.bin', '.nrg'],
        'Máquinas virtuales': ['.ova', '.ovf', '.vbox', '.vmx'],
        'Discos virtuales': ['.vdi', '.vhd', '.vhdx'],
        'Otros': ['.json', '.xml', '.html', '.htm', '.js', '.css', '.py', '.java', '.c', '.cpp']
    }
    
    for categoria, extensiones in categorias.items():
        print(f"\n   📂 {categoria}:")
        for ext in extensiones:
            max_size = MAX_FILE_SIZES.get(ext, MAX_FILE_SIZES['default'])
            if max_size >= 1024 * 1024 * 1024:
                size_str = f"{max_size / (1024 * 1024 * 1024):.0f}GB"
            else:
                size_str = f"{max_size / (1024 * 1024):.0f}MB"
            print(f"        • {ext} (máx: {size_str})")
    
    print("=" * 60)
    print("⚡ Características:")
    print("   • Soporte completo para ISOs e imágenes de disco")
    print("   • Soporte completo para OVAs y máquinas virtuales")
    print("   • Análisis automático de metadatos")
    print("   • Streaming para archivos grandes")
    print("   • Hashes SHA256 para verificación")
    print("=" * 60)
    print("🚀 Servidor iniciado. Presiona Ctrl+C para detener.")
    print("=" * 60)
    
    with socketserver.TCPServer(('', PORT), FileHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Servidor detenido")