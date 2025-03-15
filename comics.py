import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from PIL import Image, ImageTk
import mysql.connector

# ---------------- CONEXIÓN A LA BASE DE DATOS ----------------
def conectar_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Ror@$2405",  # Ajusta según tu configuración
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
            if user['rol'] == 'administrador':
                ventana_admin(user['username'])
            else:
                ventana_usuario(user['username'])
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

# ---------------- VENTANA DE VENTA/COMPRA (CON VISUALIZACIÓN DE IMAGEN) ----------------
def venta_producto(usuario):
    conn = conectar_db()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)

    # Creamos una ventana secundaria para la venta/compra
    venta = tk.Toplevel()
    venta.title("Venta de Productos")
    venta.geometry("600x500")

    tk.Label(venta, text=f"Usuario: {usuario}", font=("Arial", 12)).pack(pady=5)

    # Consultar libros (incluyendo la ruta de la imagen)
    cursor.execute("""
        SELECT producto.id_producto, 
               libro.titulo AS nombre, 
               libro.precio, 
               libro.imagen 
        FROM producto 
        JOIN libro ON producto.id_libro = libro.id_libro
    """)
    libros = cursor.fetchall()

    # Consultar revistas (incluyendo la ruta de la imagen)
    cursor.execute("""
        SELECT producto.id_producto, 
               revista.titulo AS nombre, 
               revista.precio, 
               revista.imagen 
        FROM producto 
        JOIN revista ON producto.id_revista = revista.id_revista
    """)
    revistas = cursor.fetchall()

    # Combinar los resultados
    lista_productos = libros + revistas
    productos_nombres = [f"{p['nombre']} - ${p['precio']:.2f}" for p in lista_productos]

    tk.Label(venta, text="Selecciona el producto:").pack(pady=5)
    combobox_productos = ttk.Combobox(venta, values=productos_nombres, width=50)
    combobox_productos.pack(pady=5)

    tk.Label(venta, text="Selecciona la cantidad:").pack(pady=5)
    combobox_cantidad = ttk.Combobox(venta, values=[str(i) for i in range(1, 11)], width=10)
    combobox_cantidad.pack(pady=5)

    # Label para mostrar la imagen del producto seleccionado
    label_img = tk.Label(venta)
    label_img.pack(pady=10)

    def on_seleccionar_producto(event):
        indice = combobox_productos.current()
        if indice < 0 or indice >= len(lista_productos):
            return
        ruta_imagen = lista_productos[indice].get("imagen", "")
        if ruta_imagen:
            try:
                img = Image.open(ruta_imagen)
                # Usamos el método recomendado para redimensionar la imagen, con compatibilidad para Pillow >= 10
                try:
                    resample_method = Image.Resampling.LANCZOS  # Pillow >= 10.0
                except AttributeError:
                    resample_method = Image.LANCZOS  # Versiones anteriores
                img = img.resize((150, 150), resample_method)
                img_tk = ImageTk.PhotoImage(img)
                label_img.config(image=img_tk)
                label_img.image = img_tk  # Guardamos una referencia para no perder la imagen
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

            # Verificar el stock del producto
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

            # Insertar la venta
            cursor.execute("INSERT INTO venta (fecha, monto_total, id_cliente) VALUES (NOW(), %s, 1)", (total,))
            id_venta = cursor.lastrowid

            # Determinar el tipo de producto para el detalle de la venta
            tipo_producto = 'libro' if producto in libros else 'revista'
            cursor.execute(
                "INSERT INTO detalle_venta (id_venta, id_producto, tipo_producto, cantidad, precio_unitario) VALUES (%s, %s, %s, %s, %s)",
                (id_venta, producto['id_producto'], tipo_producto, cantidad, producto['precio'])
            )

            # Actualizar el stock en el inventario
            cursor.execute("UPDATE inventario SET stock = stock - %s WHERE id_producto = %s", (cantidad, producto['id_producto']))

            conn.commit()
            messagebox.showinfo("Venta exitosa", f"Venta registrada por ${total:.2f}")
            venta.destroy()

        except ValueError:
            messagebox.showerror("Error", "Ingresa un número válido para la cantidad.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def cancelar():
        if messagebox.askyesno("Cancelar", "¿Deseas cancelar la venta?"):
            venta.destroy()

    tk.Button(venta, text="Confirmar", command=confirmar).pack(pady=10)
    tk.Button(venta, text="Cancelar", command=cancelar).pack(pady=10)

    venta.mainloop()
    conn.close()

# ---------------- CONSULTAR INVENTARIO ----------------
def consultar_inventario():
    conn = conectar_db()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)

    inventario = tk.Toplevel()
    inventario.title("Inventario Actual")
    inventario.geometry("500x400")

    tk.Label(inventario, text="Inventario de Productos", font=("Arial", 14)).pack(pady=10)

    cursor.execute("""
        SELECT producto.id_producto,
               COALESCE(libro.titulo, revista.titulo) AS nombre,
               COALESCE(libro.precio, revista.precio) AS precio,
               inventario.stock
        FROM producto
        LEFT JOIN libro ON producto.id_libro = libro.id_libro
        LEFT JOIN revista ON producto.id_revista = revista.id_revista
        JOIN inventario ON producto.id_producto = inventario.id_producto
    """)
    items = cursor.fetchall()

    for item in items:
        tk.Label(inventario, text=f"{item['nombre']} | Precio: ${item['precio']:.2f} | Stock: {item['stock']}").pack(anchor="w")

    inventario.mainloop()
    conn.close()

# ---------------- PANELES PRINCIPALES ----------------
def ventana_admin(usuario):
    admin = tk.Tk()
    admin.title(f"Panel Administrador - {usuario}")
    admin.geometry("500x400")

    tk.Label(admin, text="Bienvenido Administrador", font=("Arial", 14)).pack(pady=10)

    tk.Button(admin, text="Vender Producto", width=20, command=lambda: venta_producto(usuario)).pack(pady=10)
    tk.Button(admin, text="Consultar Inventario", width=20, command=consultar_inventario).pack(pady=10)
    tk.Button(admin, text="Cerrar Sesión", width=20, command=lambda: confirmar_cerrar_sesion(admin)).pack(pady=10)

    admin.mainloop()

def ventana_usuario(usuario):
    user = tk.Tk()
    user.title(f"Panel Usuario - {usuario}")
    user.geometry("400x300")

    tk.Label(user, text="Bienvenido Usuario", font=("Arial", 14)).pack(pady=10)

    tk.Button(user, text="Comprar Producto", width=20, command=lambda: venta_producto(usuario)).pack(pady=10)
    tk.Button(user, text="Cerrar Sesión", width=20, command=lambda: confirmar_cerrar_sesion(user)).pack(pady=10)

    user.mainloop()

def confirmar_cerrar_sesion(ventana):
    if messagebox.askyesno("Cerrar Sesión", "¿Desea cerrar sesión?"):
        ventana.destroy()
        mostrar_login()

# ---------------- INICIO DE LA APLICACIÓN ----------------
mostrar_login()
