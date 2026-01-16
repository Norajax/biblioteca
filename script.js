// Elementos del modal
const warningModal = document.getElementById('warningModal');
const acceptButton = document.getElementById('acceptButton');
const mainContainer = document.getElementById('mainContainer');
const themeToggle = document.getElementById('themeToggle');
const body = document.body;
const fileInput = document.getElementById('fileInput');
const downloadButton = document.getElementById('btnDescargar');

// Deshabilitar completamente el contenido principal al inicio
disableMainContent();

// Control del tema claro/oscuro (solo esto se guarda)
if (localStorage.getItem('darkMode') === 'true') {
    body.classList.add('dark-mode');
    if (themeToggle) themeToggle.checked = true;
}

// Alternar tema
if (themeToggle) {
    themeToggle.addEventListener('change', function() {
        body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', body.classList.contains('dark-mode'));
    });
}

// Función para deshabilitar contenido principal
function disableMainContent() {
    if (mainContainer) mainContainer.classList.add('blurred');
    if (fileInput) fileInput.disabled = true;
    if (downloadButton) downloadButton.disabled = true;
    
    // Deshabilitar toda interacción
    if (mainContainer) {
        const elements = mainContainer.querySelectorAll('*');
        elements.forEach(element => {
            element.style.pointerEvents = 'none';
        });
    }
}

// Función para habilitar contenido principal
function enableMainContent() {
    if (mainContainer) mainContainer.classList.remove('blurred');
    if (fileInput) fileInput.disabled = false;
    if (downloadButton) downloadButton.disabled = false;
    
    // Habilitar interacción
    if (mainContainer) {
        const elements = mainContainer.querySelectorAll('*');
        elements.forEach(element => {
            element.style.pointerEvents = '';
        });
    }
}

// Aceptar términos (solo para esta sesión)
if (acceptButton) {
    acceptButton.addEventListener('click', function() {
        // Animación de salida del modal
        if (warningModal) warningModal.classList.add('hidden');
        
        // Habilitar contenido principal después de la animación
        setTimeout(() => {
            enableMainContent();
            
            // Crear partículas decorativas
            createParticles();
            
            // Inicializar contenido de ejemplo
            initializeExampleContent();
            
            // Cambiar texto de carga
            const loadingElement = document.querySelector('.loading');
            if (loadingElement) {
                loadingElement.textContent = 'Cargando archivos...';
                setTimeout(() => {
                    loadingElement.style.display = 'none';
                }, 500);
            }
        }, 500);
    });
}

// Crear partículas decorativas
function createParticles() {
    const leftPanel = document.querySelector('.izquierda');
    if (!leftPanel) return;
    
    // Limpiar partículas existentes
    document.querySelectorAll('.particle').forEach(p => p.remove());
    
    for (let i = 0; i < 15; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        
        const size = Math.random() * 60 + 20;
        const posX = Math.random() * 100;
        const posY = Math.random() * 100;
        
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${posX}%`;
        particle.style.top = `${posY}%`;
        particle.style.opacity = Math.random() * 0.05 + 0.03;
        
        particle.style.animation = `float ${Math.random() * 10 + 10}s ease-in-out infinite`;
        particle.style.animationDelay = `${Math.random() * 5}s`;
        
        leftPanel.appendChild(particle);
    }
}

// Función para obtener icono según tipo de archivo
function obtenerIconoArchivo(nombreArchivo) {
    const extension = nombreArchivo.split('.').pop().toLowerCase();
    
    const iconos = {
        // Documentos
        'pdf': '📄',
        'doc': '📝',
        'docx': '📝',
        'txt': '📃',
        'rtf': '📃',
        'odt': '📝',
        
        // Hojas de cálculo
        'xls': '📊',
        'xlsx': '📊',
        'ods': '📊',
        'csv': '📈',
        
        // Presentaciones
        'ppt': '📽️',
        'pptx': '📽️',
        'odp': '📽️',
        
        // Imágenes
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'gif': '🖼️',
        'bmp': '🖼️',
        'svg': '🖼️',
        'webp': '🖼️',
        
        // Archivos comprimidos
        'zip': '📦',
        'rar': '📦',
        '7z': '📦',
        'tar': '📦',
        'gz': '📦',
        
        // Otros
        'json': '🔣',
        'xml': '📋',
        'html': '🌐',
        'htm': '🌐',
        'js': '💻',
        'css': '🎨',
        'py': '🐍',
        'java': '☕',
        'c': '🔧',
        'cpp': '🔧',
    };
    
    return iconos[extension] || '📁';
}

// Función para determinar tipo de archivo
function obtenerTipoArchivo(extension) {
    const tipos = {
        'pdf': 'documento',
        'doc': 'documento', 'docx': 'documento', 'txt': 'documento', 'rtf': 'documento', 'odt': 'documento',
        'xls': 'hoja_calculo', 'xlsx': 'hoja_calculo', 'ods': 'hoja_calculo', 'csv': 'hoja_calculo',
        'ppt': 'presentacion', 'pptx': 'presentacion', 'odp': 'presentacion',
        'jpg': 'imagen', 'jpeg': 'imagen', 'png': 'imagen', 'gif': 'imagen', 'bmp': 'imagen', 'svg': 'imagen', 'webp': 'imagen',
        'zip': 'comprimido', 'rar': 'comprimido', '7z': 'comprimido', 'tar': 'comprimido', 'gz': 'comprimido',
        'json': 'documento', 'xml': 'documento', 'html': 'documento', 'htm': 'documento',
        'js': 'documento', 'css': 'documento', 'py': 'documento', 'java': 'documento', 'c': 'documento', 'cpp': 'documento'
    };
    
    return tipos[extension] || 'documento';
}

// Crear elemento de nube para archivo
function createCloudItem(archivo) {
    const icono = obtenerIconoArchivo(archivo.nombre);
    const tamañoKB = archivo.tamaño ? Math.round(archivo.tamaño / 1024) : 'N/A';
    
    return `
        <div class="cloud-item" data-nombre="${archivo.nombre}">
            <div class="item-content">
                <input type="checkbox" class="cloud-checkbox">
                <div class="pdf-icon">${icono}</div>
                <span>${archivo.nombre}</span>
                <small style="color: var(--text-light); margin-left: 10px;">${tamañoKB} KB</small>
            </div>
        </div>
    `;
}

// Inicializar contenido de ejemplo
async function initializeExampleContent() {
    const cloudContainer = document.querySelector('.cloud-container');
    if (!cloudContainer) return;
    
    // Intentar cargar archivos reales del servidor
    try {
        await cargarArchivos();
    } catch (error) {
        console.log('Servidor no disponible, mostrando contenido de ejemplo');
        mostrarContenidoEjemplo();
    }
}

// Función para cargar archivos del servidor
async function cargarArchivos() {
    try {
        const response = await fetch('/files'); // Cambiado de '/pdfs' a '/files'
        const archivos = await response.json();
        mostrarArchivos(archivos);
        return archivos;
    } catch (error) {
        console.error('Error al cargar archivos:', error);
        throw error;
    }
}

// Mostrar archivos en la nube
function mostrarArchivos(archivos) {
    const cloudContainer = document.querySelector('.cloud-container');
    if (!cloudContainer) return;
    
    // Agrupar por tipo de archivo
    const agrupados = {};
    
    archivos.forEach(archivo => {
        const tipo = archivo.tipo || obtenerTipoArchivo(archivo.extension || archivo.nombre.split('.').pop().toLowerCase());
        if (!agrupados[tipo]) {
            agrupados[tipo] = [];
        }
        agrupados[tipo].push(archivo);
    });
    
    let html = '';
    
    Object.keys(agrupados).forEach(tipo => {
        // Traducir tipo a nombre más amigable
        const nombresTipo = {
            'documento': '📝 Documentos',
            'imagen': '🖼️ Imágenes',
            'comprimido': '📦 Archivos Comprimidos',
            'hoja_calculo': '📊 Hojas de Cálculo',
            'presentacion': '📽️ Presentaciones'
        };
        
        html += `<div class="categoria">${nombresTipo[tipo] || '📁 Archivos'}</div>`;
        
        agrupados[tipo].forEach(archivo => {
            html += createCloudItem(archivo);
        });
    });
    
    cloudContainer.innerHTML = html;
    
    // Añadir interactividad a los elementos de la nube
    const cloudItems = document.querySelectorAll('.cloud-item');
    cloudItems.forEach(item => {
        item.addEventListener('click', function(e) {
            if (!e.target.classList.contains('cloud-checkbox')) {
                // Seleccionar/deseleccionar el checkbox
                const checkbox = this.querySelector('.cloud-checkbox');
                checkbox.checked = !checkbox.checked;
                this.classList.toggle('selected', checkbox.checked);
            }
        });
        
        // Hacer clic en el icono para visualizar
        const icon = item.querySelector('.pdf-icon');
        if (icon) {
            icon.addEventListener('click', function(e) {
                e.stopPropagation();
                const nombreArchivo = item.getAttribute('data-nombre');
                visualizarArchivo(nombreArchivo);
            });
        }
    });
}

// Mostrar contenido de ejemplo si no hay servidor
function mostrarContenidoEjemplo() {
    const cloudContainer = document.querySelector('.cloud-container');
    if (!cloudContainer) return;
    
    const archivosEjemplo = [
        { nombre: 'Informe_Financiero.pdf', tipo: 'documento', tamaño: 1024 * 250 }, // 250 KB
        { nombre: 'Contrato_Servicios.docx', tipo: 'documento', tamaño: 1024 * 180 },
        { nombre: 'Manual_Usuario.txt', tipo: 'documento', tamaño: 1024 * 120 },
        { nombre: 'Graficos_Proyecto.png', tipo: 'imagen', tamaño: 1024 * 800 },
        { nombre: 'Datos_Ventas.xlsx', tipo: 'hoja_calculo', tamaño: 1024 * 350 },
        { nombre: 'Presentacion_Clientes.pptx', tipo: 'presentacion', tamaño: 1024 * 4500 },
        { nombre: 'Backup_Archivos.zip', tipo: 'comprimido', tamaño: 1024 * 2200 },
        { nombre: 'Configuracion.json', tipo: 'documento', tamaño: 1024 * 5 },
        { nombre: 'Codigo_Fuente.py', tipo: 'documento', tamaño: 1024 * 15 },
        { nombre: 'Fotos_Vacaciones.jpg', tipo: 'imagen', tamaño: 1024 * 1200 }
    ];
    
    mostrarArchivos(archivosEjemplo);
}

// Visualizar archivo según su tipo
function visualizarArchivo(nombreArchivo) {
    const extension = nombreArchivo.split('.').pop().toLowerCase();
    const visor = document.getElementById('visor');
    const icono = obtenerIconoArchivo(nombreArchivo);
    
    visor.classList.add('has-content');
    
    // Para imágenes
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'].includes(extension)) {
        visor.innerHTML = `
            <div style="text-align: center; padding: 20px; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <h3 style="margin-bottom: 20px;">${nombreArchivo}</h3>
                <div style="flex: 1; display: flex; align-items: center; justify-content: center; width: 100%;">
                    <img src="/uploads/${encodeURIComponent(nombreArchivo)}" 
                         style="max-width: 100%; max-height: 70vh; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.2);">
                </div>
                <div style="margin-top: 20px;">
                    <a href="/uploads/${encodeURIComponent(nombreArchivo)}" download 
                       style="background: var(--accent-color); color: white; padding: 10px 20px; border-radius: 10px; text-decoration: none;">
                        📥 Descargar Imagen
                    </a>
                </div>
            </div>`;
    }
    // Para PDFs
    else if (extension === 'pdf') {
        visor.innerHTML = `
            <iframe src="/uploads/${encodeURIComponent(nombreArchivo)}" 
                    style="width: 100%; height: 100%; border: none;"></iframe>`;
    }
    // Para otros tipos
    else {
        visor.innerHTML = `
            <div style="text-align: center; padding: 40px; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <div style="font-size: 4rem; margin-bottom: 20px;">${icono}</div>
                <h3>${nombreArchivo}</h3>
                <p style="margin: 20px 0;">Este tipo de archivo no se puede visualizar directamente en el navegador.</p>
                <div>
                    <a href="/uploads/${encodeURIComponent(nombreArchivo)}" download 
                       style="background: linear-gradient(135deg, var(--accent-color), var(--dark-color)); 
                              color: white; padding: 12px 25px; border-radius: 10px; 
                              text-decoration: none; display: inline-block; font-weight: 600;">
                        📥 Descargar Archivo
                    </a>
                </div>
            </div>`;
    }
    
    // Desplazar visor a la vista
    visor.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Manejo del botón de descargar
if (downloadButton) {
    downloadButton.addEventListener('click', async function() {
        const checkedItems = document.querySelectorAll('.cloud-checkbox:checked');
        if (checkedItems.length === 0) {
            alert('Selecciona al menos un archivo para descargar');
            return;
        }
        
        const archivos = [];
        checkedItems.forEach(item => {
            const cloudItem = item.closest('.cloud-item');
            if (cloudItem) {
                archivos.push(cloudItem.getAttribute('data-nombre'));
            }
        });
        
        if (archivos.length === 1) {
            // Descargar archivo individual
            const link = document.createElement('a');
            link.href = `/uploads/${encodeURIComponent(archivos[0])}`;
            link.download = archivos[0];
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            // Descargar múltiples archivos (necesitarías ZIP en el backend)
            alert(`Preparando descarga de ${archivos.length} archivos...\n\nPara descargar múltiples archivos, el servidor debe soportar ZIP.`);
            
            // Alternativa: descargar uno por uno
            /*
            for (let archivo of archivos) {
                const link = document.createElement('a');
                link.href = `/uploads/${encodeURIComponent(archivo)}`;
                link.download = archivo;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                await new Promise(resolve => setTimeout(resolve, 500));
            }
            */
        }
    });
}

// Manejo de subida de archivos
if (fileInput) {
    fileInput.addEventListener('change', async function(e) {
        if (!this.files || this.files.length === 0) return;
        
        const archivo = this.files[0];
        const extension = archivo.name.split('.').pop().toLowerCase();
        
        // Extensiones permitidas (debe coincidir con el servidor)
        const extensionesPermitidas = [
            'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
            'xls', 'xlsx', 'ods', 'csv',
            'ppt', 'pptx', 'odp',
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp',
            'zip', 'rar', '7z', 'tar', 'gz',
            'json', 'xml', 'html', 'htm', 'js', 'css', 'py', 'java', 'c', 'cpp'
        ];
        
        if (!extensionesPermitidas.includes(extension)) {
            alert(`Tipo de archivo no permitido: .${extension}\n\nSolo se permiten: ${extensionesPermitidas.join(', ')}`);
            this.value = '';
            return;
        }
        
    
        
        // Subir archivo
        const formData = new FormData();
        formData.append('file', archivo);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Error al subir archivo');
            }
            
            const data = await response.json();
            alert(`Archivo "${archivo.name}" subido correctamente`);
            this.value = '';
            
            // Recargar lista de archivos
            await cargarArchivos();
            
        } catch (error) {
            console.error('Error al subir archivo:', error);
            alert(`Error al subir archivo: ${error.message}`);
            this.value = '';
        }
    });
}

// Función debounce para optimización
function debounce(func, wait) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Si el usuario intenta recargar la página, el aviso aparecerá de nuevo
window.addEventListener('beforeunload', function(e) {
    // No hacemos nada especial aquí
});