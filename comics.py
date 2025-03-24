import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import mysql.connector

# ---------------- CONEXIÓN A LA BASE DE DATOS ----------------
def conectar_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Ror@$2405",  # Se ajusta según la configuración
            database="sistema_libreria"
        )
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Error de conexión", f"No se pudo conectar a la base de datos:\n{err}")
        return None

# ---------------- FUNCIONES DE LOGIN ----------------
def verificar_login():
    usuario = entry_usuario.get()
    password = entry_password.get()

    conn = conectar_db()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuario WHERE username = %s AND password = %s", (usuario, password))
        user = cursor.fetchone()

        if user:
            root.destroy()  # Cierra la ventana de login
            ventana_principal(user['username'])
        else:
            messagebox.showerror("Login fallido", "Usuario o contraseña incorrectos.")
        conn.close()

def mostrar_login():
    global root, entry_usuario, entry_password
    root = tk.Tk()
    root.title("Login Sistema Librería")
    root.geometry("350x200")

    tk.Label(root, text="Usuario:").pack(pady=5)
    entry_usuario = tk.Entry(root)
    entry_usuario.pack()

    tk.Label(root, text="Contraseña:").pack(pady=5)
    entry_password = tk.Entry(root, show="*")
    entry_password.pack()

    tk.Button(root, text="Iniciar Sesión", command=verificar_login).pack(pady=10)
    tk.Button(root, text="Salir", command=root.quit).pack(pady=5)

    root.mainloop()

# ---------------- VENTANA DE VENTA/COMPRA ----------------
def venta_producto(usuario):
    conn = conectar_db()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)

    venta = tk.Toplevel()
    venta.title("Venta de Productos")
    venta.geometry("600x550")

    tk.Label(venta, text=f"Usuario: {usuario}", font=("Arial", 12)).pack(pady=5)

    cursor.execute("SELECT id_cliente, nombre FROM cliente")
    clientes = cursor.fetchall()
    clientes_nombres = [f"{c['nombre']}" for c in clientes]

    tk.Label(venta, text="Selecciona el cliente:").pack(pady=5)
    combobox_cliente = ttk.Combobox(venta, values=clientes_nombres, width=50)
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
    """)
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
    """)
    revistas = cursor.fetchall()

    lista_productos = libros + revistas
    productos_nombres = [f"{p['nombre']} - ${p['precio']:.2f}" for p in lista_productos]

    tk.Label(venta, text="Selecciona el producto:").pack(pady=5)
    combobox_productos = ttk.Combobox(venta, values=productos_nombres, width=50)
    combobox_productos.pack(pady=5)

    tk.Label(venta, text="Selecciona la cantidad:").pack(pady=5)
    combobox_cantidad = ttk.Combobox(venta, values=[str(i) for i in range(1, 11)], width=10)
    combobox_cantidad.pack(pady=5)

    label_img = tk.Label(venta)
    label_img.pack(pady=10)

    label_info = tk.Label(venta, text="", justify="left", font=("Arial", 10))
    label_info.pack(pady=5)

    def on_seleccionar_producto(event):
        indice = combobox_productos.current()
        if indice < 0 or indice >= len(lista_productos):
            return

        producto = lista_productos[indice]
        ruta_imagen = producto.get("imagen", "")

        if producto["tipo"] == "libro":
            info_text = (
                f"ISBN: {producto.get('ISBN', 'N/D')}\n"
                f"Año de publicación: {producto.get('año_publicacion', 'N/D')}\n"
                f"Editorial: {producto.get('editorial', 'N/D')}"
            )
        elif producto["tipo"] == "revista":
            info_text = (
                f"ISSN: {producto.get('ISSN', 'N/D')}\n"
                f"Periodicidad: {producto.get('periodicidad', 'N/D')}\n"
                f"Editorial: {producto.get('editorial', 'N/D')}"
            )
        else:
            info_text = ""
        label_info.config(text=info_text)

        if ruta_imagen:
            try:
                img = Image.open(ruta_imagen)
                try:
                    resample_method = Image.Resampling.LANCZOS
                except AttributeError:
                    resample_method = Image.LANCZOS
                img = img.resize((150, 150), resample_method)
                img_tk = ImageTk.PhotoImage(img)
                label_img.config(image=img_tk)
                label_img.image = img_tk
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la imagen: {e}")
        else:
            label_img.config(image="")
            label_img.image = None

    combobox_productos.bind("<<ComboboxSelected>>", on_seleccionar_producto)

    def confirmar():
        try:
            indice = combobox_productos.current()
            if indice < 0 or indice >= len(lista_productos):
                messagebox.showerror("Error", "Selecciona un producto válido.")
                return

            cantidad = int(combobox_cantidad.get())
            if cantidad <= 0:
                messagebox.showerror("Error", "Cantidad inválida.")
                return

            producto = lista_productos[indice]

            cursor.execute("SELECT stock FROM inventario WHERE id_producto = %s", (producto['id_producto'],))
            stock_registro = cursor.fetchone()
            if not stock_registro:
                messagebox.showerror("Error", "No se encontró registro de stock para este producto.")
                return

            stock = stock_registro['stock']
            if cantidad > stock:
                messagebox.showwarning("Stock insuficiente", f"Solo hay {stock} unidades disponibles.")
                return

            total = cantidad * producto['precio']

            # Seleccionar cliente
            cliente_seleccionado = combobox_cliente.get()
            cursor.execute("SELECT id_cliente FROM cliente WHERE nombre = %s", (cliente_seleccionado,))
            cliente = cursor.fetchone()
            if not cliente:
                messagebox.showerror("Error", "No se encontró el cliente seleccionado.")
                return

            id_cliente = cliente['id_cliente']

            cursor.execute("INSERT INTO venta (fecha, monto_total, id_cliente) VALUES (NOW(), %s, %s)", (total, id_cliente))
            id_venta = cursor.lastrowid

            tipo_producto = producto['tipo']
            cursor.execute(
                "INSERT INTO detalle_venta (id_venta, id_producto, tipo_producto, cantidad, precio_unitario) VALUES (%s, %s, %s, %s, %s)",
                (id_venta, producto['id_producto'], tipo_producto, cantidad, producto['precio'])
            )

            cursor.execute("UPDATE inventario SET stock = stock - %s WHERE id_producto = %s", (cantidad, producto['id_producto']))

            conn.commit()

            messagebox.showinfo("Venta exitosa",
                f"Venta registrada:\n"
                f"Producto: {producto['nombre']}\n"
                f"Cantidad: {cantidad}\n"
                f"Precio total: ${total:.2f}"
            )
            venta.destroy()

        except ValueError:
            messagebox.showerror("Error", "Ingresa un número válido para la cantidad.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def cancelar():
        if messagebox.askyesno("Cancelar", "¿Deseas cancelar la venta?"):
            venta.destroy()

    tk.Button(venta, text="Confirmar", command=confirmar).pack(pady=5)
    tk.Button(venta, text="Cancelar", command=cancelar).pack(pady=5)

    venta.mainloop()

# ---------------- FUNCIONES PARA VENTAS TOP Y CLIENTES TOP ----------------
def mostrar_top_ventas():
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
    """)
    ventas_top = cursor.fetchall()
    conn.close()

    ventana_top_ventas = tk.Toplevel()
    ventana_top_ventas.title("Top 10 Ventas")
    ventana_top_ventas.geometry("600x400")

    for idx, venta in enumerate(ventas_top, start=1):
        tk.Label(ventana_top_ventas, text=f"Venta {idx}: {venta['fecha']} - Total: ${venta['monto_total']:.2f}").pack(pady=5)

def mostrar_top_clientes():
    conn = conectar_db()
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
    """)
    clientes_top = cursor.fetchall()
    conn.close()

    ventana_top_clientes = tk.Toplevel()
    ventana_top_clientes.title("Top 10 Clientes")
    ventana_top_clientes.geometry("600x400")

    for idx, cliente in enumerate(clientes_top, start=1):
        tk.Label(ventana_top_clientes, text=f"Cliente {idx}: {cliente['nombre']} - Total Comprado: ${cliente['monto_total']:.2f}").pack(pady=5)

def mostrar_inventario():
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
    """)
    productos = cursor.fetchall()
    conn.close()

    ventana_inventario = tk.Toplevel()
    ventana_inventario.title("Inventario")
    ventana_inventario.geometry("700x500")

    for producto in productos:
        tk.Label(ventana_inventario, text=f"{producto['nombre_producto']} - Stock: {producto['stock']} - Tipo: {producto['tipo_producto']}").pack(pady=5)

# ---------------- VENTANA PRINCIPAL ----------------
def ventana_principal(usuario):
    ventana = tk.Tk()
    ventana.title("Sistema de Librería")
    ventana.geometry("600x500")

    tk.Label(ventana, text=f"Bienvenido, {usuario}", font=("Arial", 12)).pack(pady=10)

    tk.Button(ventana, text="Venta de productos", command=lambda: venta_producto(usuario)).pack(pady=10)
    tk.Button(ventana, text="Top de ventas", command=mostrar_top_ventas).pack(pady=10)
    tk.Button(ventana, text="Top de clientes", command=mostrar_top_clientes).pack(pady=10)
    tk.Button(ventana, text="Inventario", command=mostrar_inventario).pack(pady=10)

    def cerrar_sesion():
        if messagebox.askyesno("Cerrar sesión", "¿Estás seguro de que deseas cerrar sesión?"):
            ventana.destroy()
            mostrar_login()

    tk.Button(ventana, text="Cerrar sesión", command=cerrar_sesion).pack(pady=10)

    ventana.mainloop()

# Mostrar ventana de login
mostrar_login()
