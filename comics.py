import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import mysql.connector

# ---------------- CONEXIÓN A LA BASE DE DATOS ----------------
def conectar_db(): # Función para conectar a la base de datos
    try: # Intenta conectarse a la base de datos
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Saltamontes71#",  # Se ajusta según la configuración
            database="sistema_libreria"
        )
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Error de conexión", f"No se pudo conectar a la base de datos:\n{err}") # Mensaje de error
        return None

# ---------------- FUNCIONES DE LOGIN ----------------
def verificar_login(): # Función para verificar el login
    usuario = entry_usuario.get() # Obtiene el usuario ingresado
    password = entry_password.get() # Obtiene la contraseña ingresada

    conn = conectar_db()
    if conn:
        cursor = conn.cursor(dictionary=True) # Cursor para ejecutar consultas
        cursor.execute("SELECT * FROM usuario WHERE username = %s AND password = %s", (usuario, password)) # Consulta para verificar el usuario
        user = cursor.fetchone()

        if user:
            root.destroy()  # Cierra la ventana de login
            ventana_principal(user['username']) # Abre la ventana principal
        else:
            messagebox.showerror("Login fallido", "Usuario o contraseña incorrectos.") # Mensaje de error
        conn.close()

def mostrar_login(): # Función para mostrar la ventana de login
    global root, entry_usuario, entry_password
    root = tk.Tk()
    root.title("Login Sistema Librería") # Título de la ventana
    root.geometry("350x200")

    tk.Label(root, text="Usuario:").pack(pady=5) # Etiqueta para el usuario
    entry_usuario = tk.Entry(root)
    entry_usuario.pack()

    tk.Label(root, text="Contraseña:").pack(pady=5) # Etiqueta para la contraseña
    entry_password = tk.Entry(root, show="*")
    entry_password.pack()

    tk.Button(root, text="Iniciar Sesión", command=verificar_login).pack(pady=10) # Botón para iniciar sesión
    tk.Button(root, text="Salir", command=root.quit).pack(pady=5) # Botón para salir

    root.mainloop() # Mantiene la ventana abierta

# ---------------- VENTANA DE VENTA/COMPRA ----------------
def venta_producto(usuario):  # Función para realizar una venta
    conn = conectar_db() # Conexión a la base de datos
    if not conn:
        return
    cursor = conn.cursor(dictionary=True) # Cursor para ejecutar consultas

    venta = tk.Toplevel()
    venta.title("Venta de Productos") # Título de la ventana
    venta.geometry("600x550")

    tk.Label(venta, text=f"Usuario: {usuario}", font=("Arial", 12)).pack(pady=5) # Etiqueta con el usuario

    cursor.execute("SELECT id_cliente, nombre FROM cliente") # Consulta para obtener los clientes
    clientes = cursor.fetchall() # Lista con los clientes
    clientes_nombres = [f"{c['nombre']}" for c in clientes] # Lista con los nombres de los clientes

    tk.Label(venta, text="Selecciona el cliente:").pack(pady=5) # Etiqueta para seleccionar el cliente
    combobox_cliente = ttk.Combobox(venta, values=clientes_nombres, width=50) # Combobox para seleccionar el cliente
    combobox_cliente.pack(pady=5)

    cursor.execute("""  
        SELECT producto.id_producto, 
               libro.titulo AS nombre, 
               libro.precio, 
               libro.imagen,
               libro.ISBN,
               libro.año_publicacion,
               editorial.nombre AS editorial,
               'libro' AS tipo
        FROM producto 
        JOIN libro ON producto.id_libro = libro.id_libro
        JOIN editorial ON libro.id_editorial = editorial.id_editorial
    """) # Consulta para obtener los libros
    libros = cursor.fetchall()

    cursor.execute("""  
        SELECT producto.id_producto, 
               revista.titulo AS nombre, 
               revista.precio, 
               revista.imagen,
               revista.ISSN,
               revista.periodicidad,
               editorial.nombre AS editorial,
               'revista' AS tipo
        FROM producto 
        JOIN revista ON producto.id_revista = revista.id_revista
        JOIN editorial ON revista.id_editorial = editorial.id_editorial
    """) # Consulta para obtener las revistas
    revistas = cursor.fetchall()

    lista_productos = libros + revistas
    productos_nombres = [f"{p['nombre']} - ${p['precio']:.2f}" for p in lista_productos] # Lista con los nombres de los productos

    tk.Label(venta, text="Selecciona el producto:").pack(pady=5) # Etiqueta para seleccionar el producto
    combobox_productos = ttk.Combobox(venta, values=productos_nombres, width=50)
    combobox_productos.pack(pady=5)

    tk.Label(venta, text="Selecciona la cantidad:").pack(pady=5) # Etiqueta para seleccionar la cantidad
    combobox_cantidad = ttk.Combobox(venta, values=[str(i) for i in range(1, 11)], width=10)
    combobox_cantidad.pack(pady=5)

    label_img = tk.Label(venta)
    label_img.pack(pady=10)

    label_info = tk.Label(venta, text="", justify="left", font=("Arial", 10))
    label_info.pack(pady=5)

    def on_seleccionar_producto(event): # Función para seleccionar un producto
        indice = combobox_productos.current() # Obtiene el índice del producto seleccionado
        if indice < 0 or indice >= len(lista_productos): # Si el índice es inválido
            return

        producto = lista_productos[indice] # Obtiene el producto seleccionado
        ruta_imagen = producto.get("imagen", "") # Obtiene la ruta de la imagen del producto

        if producto["tipo"] == "libro": # Si el producto es un libro
            info_text = (
                f"ISBN: {producto.get('ISBN', 'N/D')}\n"
                f"Año de publicación: {producto.get('año_publicacion', 'N/D')}\n"
                f"Editorial: {producto.get('editorial', 'N/D')}"
            ) # Texto con la información del libro
        elif producto["tipo"] == "revista": # Si el producto es una revista
            info_text = (
                f"ISSN: {producto.get('ISSN', 'N/D')}\n"
                f"Periodicidad: {producto.get('periodicidad', 'N/D')}\n"
                f"Editorial: {producto.get('editorial', 'N/D')}"
            ) # Texto con la información de la revista
        else:
            info_text = ""
        label_info.config(text=info_text) # Muestra la información del producto

        if ruta_imagen: # Si hay una imagen
            try:
                img = Image.open(ruta_imagen) # Abre la imagen
                try:
                    resample_method = Image.Resampling.LANCZOS # Método de resample
                except AttributeError:
                    resample_method = Image.LANCZOS
                img = img.resize((150, 150), resample_method) # Redimensiona la imagen
                img_tk = ImageTk.PhotoImage(img)
                label_img.config(image=img_tk)
                label_img.image = img_tk
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la imagen: {e}") # Mensaje de error
        else:
            label_img.config(image="")
            label_img.image = None

    combobox_productos.bind("<<ComboboxSelected>>", on_seleccionar_producto) # Llama a la función al seleccionar un producto

    def confirmar():
        try:
            indice = combobox_productos.current() # Obtiene el índice del producto seleccionado
            if indice < 0 or indice >= len(lista_productos):
                messagebox.showerror("Error", "Selecciona un producto válido.") # Mensaje de error
                return

            cantidad = int(combobox_cantidad.get()) # Obtiene la cantidad ingresada
            if cantidad <= 0: # Si la cantidad es inválida
                messagebox.showerror("Error", "Cantidad inválida.")
                return

            producto = lista_productos[indice] # Obtiene el producto seleccionado

            cursor.execute("SELECT stock FROM inventario WHERE id_producto = %s", (producto['id_producto'],)) # Consulta para obtener el stock del producto
            stock_registro = cursor.fetchone() # Registro con el stock del producto
            if not stock_registro:
                messagebox.showerror("Error", "No se encontró registro de stock para este producto.") # Mensaje de error
                return

            stock = stock_registro['stock'] # Obtiene el stock del producto
            if cantidad > stock:
                messagebox.showwarning("Stock insuficiente", f"Solo hay {stock} unidades disponibles.") # Mensaje de advertencia
                return

            total = cantidad * producto['precio'] # Calcula el total de la venta

            # Seleccionar cliente
            cliente_seleccionado = combobox_cliente.get() # Obtiene el cliente seleccionado
            cursor.execute("SELECT id_cliente FROM cliente WHERE nombre = %s", (cliente_seleccionado,)) # Consulta para obtener el id del cliente
            cliente = cursor.fetchone()
            if not cliente:
                messagebox.showerror("Error", "No se encontró el cliente seleccionado.") # Mensaje de error
                return

            id_cliente = cliente['id_cliente'] # Obtiene el id del cliente

            cursor.execute("INSERT INTO venta (fecha, monto_total, id_cliente) VALUES (NOW(), %s, %s)", (total, id_cliente)) # Inserta la venta en la base de datos
            id_venta = cursor.lastrowid

            tipo_producto = producto['tipo'] # Obtiene el tipo del producto
            cursor.execute(
                "INSERT INTO detalle_venta (id_venta, id_producto, tipo_producto, cantidad, precio_unitario) VALUES (%s, %s, %s, %s, %s)", # Inserta el detalle de la venta en la base de datos
                (id_venta, producto['id_producto'], tipo_producto, cantidad, producto['precio']) # Valores a insertar
            )

            cursor.execute("UPDATE inventario SET stock = stock - %s WHERE id_producto = %s", (cantidad, producto['id_producto']))  # Actualiza el stock del producto

            conn.commit()

            messagebox.showinfo("Venta exitosa", # Mensaje de éxito
                f"Venta registrada:\n" # Mensaje con la información de la venta
                f"Producto: {producto['nombre']}\n" #   Nombre del producto
                f"Cantidad: {cantidad}\n" #   Cantidad
                f"Precio total: ${total:.2f}" #   Precio total
            )
            venta.destroy() # Cierra la ventana de venta

        except ValueError:
            messagebox.showerror("Error", "Ingresa un número válido para la cantidad.") # Mensaje de error
        except Exception as e:
            messagebox.showerror("Error", str(e)) # Mensaje de error

    def cancelar():
        if messagebox.askyesno("Cancelar", "¿Deseas cancelar la venta?"): # Pregunta si se desea cancelar la venta
            venta.destroy()

    tk.Button(venta, text="Confirmar", command=confirmar).pack(pady=5) # Botón para confirmar la venta
    tk.Button(venta, text="Cancelar", command=cancelar).pack(pady=5) # Botón para cancelar la venta

    venta.mainloop() # Mantiene la ventana abierta

# ---------------- FUNCIONES PARA VENTAS TOP Y CLIENTES TOP ----------------
def mostrar_top_ventas(): # Función para mostrar las ventas top
    conn = conectar_db()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT v.id_venta, v.fecha, SUM(dv.cantidad * dv.precio_unitario) AS monto_total
        FROM venta v
        JOIN detalle_venta dv ON v.id_venta = dv.id_venta
        GROUP BY v.id_venta
        ORDER BY monto_total DESC
        LIMIT 10
    """) # Consulta para obtener las ventas top
    ventas_top = cursor.fetchall()
    conn.close()

    ventana_top_ventas = tk.Toplevel() # Ventana para mostrar las ventas top
    ventana_top_ventas.title("Top 10 Ventas") # Título de la ventana
    ventana_top_ventas.geometry("600x400") # Tamaño de la ventana

    for idx, venta in enumerate(ventas_top, start=1): # Recorre las ventas top
        tk.Label(ventana_top_ventas, text=f"Venta {idx}: {venta['fecha']} - Total: ${venta['monto_total']:.2f}").pack(pady=5)

def mostrar_top_clientes(): # Función para mostrar los clientes top
    conn = conectar_db() # Conexión a la base de datos
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.id_cliente, c.nombre, SUM(dv.cantidad * dv.precio_unitario) AS monto_total
        FROM cliente c
        JOIN venta v ON c.id_cliente = v.id_cliente
        JOIN detalle_venta dv ON v.id_venta = dv.id_venta
        GROUP BY c.id_cliente
        ORDER BY monto_total DESC
        LIMIT 10
    """) # Consulta para obtener los clientes top
    clientes_top = cursor.fetchall()
    conn.close()

    ventana_top_clientes = tk.Toplevel()
    ventana_top_clientes.title("Top 10 Clientes")
    ventana_top_clientes.geometry("600x400")

    for idx, cliente in enumerate(clientes_top, start=1):
        tk.Label(ventana_top_clientes, text=f"Cliente {idx}: {cliente['nombre']} - Total Comprado: ${cliente['monto_total']:.2f}").pack(pady=5) # Muestra el cliente top

def mostrar_inventario(): # Función para mostrar el inventario
    conn = conectar_db()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.id_producto, 
               COALESCE(l.titulo, r.titulo) AS nombre_producto, 
               i.stock, 
               i.tipo_producto
        FROM inventario i
        JOIN producto p ON i.id_producto = p.id_producto
        LEFT JOIN libro l ON p.id_libro = l.id_libro
        LEFT JOIN revista r ON p.id_revista = r.id_revista
    """) # Consulta para obtener el inventario
    productos = cursor.fetchall()
    conn.close() # Cierra la conexión

    ventana_inventario = tk.Toplevel()
    ventana_inventario.title("Inventario")
    ventana_inventario.geometry("700x500")

    for producto in productos:
        tk.Label(ventana_inventario, text=f"{producto['nombre_producto']} - Stock: {producto['stock']} - Tipo: {producto['tipo_producto']}").pack(pady=5) # Muestra el producto y su stock

# ---------------- VENTANA PRINCIPAL ----------------
def ventana_principal(usuario):
    ventana = tk.Tk()
    ventana.title("Sistema de Librería")
    ventana.geometry("600x500")

    tk.Label(ventana, text=f"Bienvenido, {usuario}", font=("Arial", 12)).pack(pady=10)

    tk.Button(ventana, text="Venta de productos", command=lambda: venta_producto(usuario)).pack(pady=10) # Botón para venta de productos
    tk.Button(ventana, text="Top de ventas", command=mostrar_top_ventas).pack(pady=10) # Botón para ventas top
    tk.Button(ventana, text="Top de clientes", command=mostrar_top_clientes).pack(pady=10) # Botón para clientes top
    tk.Button(ventana, text="Inventario", command=mostrar_inventario).pack(pady=10) # Botón para mostrar el inventario

    def cerrar_sesion():
        if messagebox.askyesno("Cerrar sesión", "¿Estás seguro de que deseas cerrar sesión?"): # Pregunta si se desea cerrar sesión
            ventana.destroy()
            mostrar_login()

    tk.Button(ventana, text="Cerrar sesión", command=cerrar_sesion).pack(pady=10) # Botón para cerrar sesión

    ventana.mainloop() # Mantiene la ventana abierta

# Mostrar ventana de login
mostrar_login() # Llama a la función para mostrar el login
