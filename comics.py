import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import mysql.connector

# ---------------- CONEXIÓN A LA BASE DE DATOS ----------------
def conectar_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Saltamontes71#",  # Cambia si tienes contraseña
            database="sistema_libreria"
        )
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Error de conexión", f"No se pudo conectar a la base de datos:\n{err}")
        return None

# ---------------- LOGIN ----------------
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

# ---------------- VENTANAS ----------------
def ventana_admin(usuario):
    admin = tk.Tk()
    admin.title(f"Panel Administrador - {usuario}")
    admin.geometry("500x400")

    tk.Label(admin, text="Bienvenido Administrador", font=("Arial", 14)).pack(pady=10)

    btn_vender = tk.Button(admin, text="Vender Producto", width=20, command=lambda: venta_producto(usuario))
    btn_inventario = tk.Button(admin, text="Consultar Inventario", width=20, command=consultar_inventario)
    btn_logout = tk.Button(admin, text="Cerrar Sesión", width=20, command=lambda: confirmar_cerrar_sesion(admin))

    btn_vender.pack(pady=10)
    btn_inventario.pack(pady=10)
    btn_logout.pack(pady=10)

    admin.mainloop()

def ventana_usuario(usuario):
    user = tk.Tk()
    user.title(f"Panel Usuario - {usuario}")
    user.geometry("400x300")

    tk.Label(user, text="Bienvenido Usuario", font=("Arial", 14)).pack(pady=10)

    btn_vender = tk.Button(user, text="Vender Producto", width=20, command=lambda: venta_producto(usuario))
    btn_logout = tk.Button(user, text="Cerrar Sesión", width=20, command=lambda: confirmar_cerrar_sesion(user))

    btn_vender.pack(pady=10)
    btn_logout.pack(pady=10)

    user.mainloop()

# ---------------- VOLVER AL LOGIN ----------------
def confirmar_cerrar_sesion(ventana):
    respuesta = messagebox.askyesno("Cerrar Sesión", "¿Está seguro que quiere cerrar sesión?")
    if respuesta:  # Si elige "Sí", cerrar sesión
        ventana.destroy()
        mostrar_login()

def volver_al_login(admin):
    admin.destroy()  # Cierra la ventana actual de administrador
    mostrar_login()  # Vuelve a mostrar la ventana de login

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

    btn_login = tk.Button(root, text="Iniciar Sesión", command=verificar_login)
    btn_salir = tk.Button(root, text="Salir", command=root.quit)

    btn_login.pack(pady=10)
    btn_salir.pack(pady=5)

    root.mainloop()

# ---------------- VENDER PRODUCTO ----------------
def venta_producto(usuario):
    conn = conectar_db()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)

    venta = tk.Tk()
    venta.title("Venta de Productos")
    venta.geometry("600x400")

    tk.Label(venta, text=f"Vendedor: {usuario}", font=("Arial", 12)).pack(pady=5)

    productos_frame = tk.Frame(venta)
    productos_frame.pack()

    # Mostrar libros
    cursor.execute("SELECT producto.id_producto, libro.título AS nombre, libro.precio FROM producto JOIN libro ON producto.id_libro = libro.id_libro")
    libros = cursor.fetchall()

    # Mostrar revistas
    cursor.execute("SELECT producto.id_producto, revista.titulo AS nombre, revista.precio FROM producto JOIN revista ON producto.id_revista = revista.id_revista")
    revistas = cursor.fetchall()

    lista_productos = libros + revistas

    # Crear ComboBox para productos
    productos_nombres = [f"{prod['nombre']} - ${prod['precio']:.2f}" for prod in lista_productos]
    tk.Label(venta, text="Selecciona el producto:").pack(pady=5)
    combobox_productos = ttk.Combobox(venta, values=productos_nombres, width=50)
    combobox_productos.pack()

    # Crear ComboBox para seleccionar la cantidad (1-10)
    tk.Label(venta, text="Selecciona la cantidad:").pack(pady=5)
    combobox_cantidad = ttk.Combobox(venta, values=[str(i) for i in range(1, 11)])
    combobox_cantidad.pack()

    def confirmar():
        try:
            seleccion = combobox_productos.current()
            cantidad = int(combobox_cantidad.get())

            if seleccion < 0 or seleccion >= len(lista_productos):
                messagebox.showerror("Error", "Selección inválida.")
                return
            if cantidad <= 0:
                messagebox.showerror("Error", "Cantidad inválida.")
                return

            producto = lista_productos[seleccion]

            # Verificar stock
            cursor.execute("SELECT stock FROM inventario WHERE id_producto = %s", (producto['id_producto'],))
            stock = cursor.fetchone()['stock']

            if cantidad > stock:
                messagebox.showwarning("Stock insuficiente", f"Solo hay {stock} unidades disponibles.")
                return

            total = cantidad * producto['precio']

            # Insertar venta
            cursor.execute("INSERT INTO venta (fecha, monto_total, id_cliente) VALUES (NOW(), %s, 1)", (total,))
            id_venta = cursor.lastrowid

            tipo = 'libro' if producto in libros else 'revista'

            # Insertar detalle venta
            cursor.execute("INSERT INTO detalle_venta (id_venta, id_producto, tipo_producto, cantidad, precio_unitario) VALUES (%s, %s, %s, %s, %s)",
                           (id_venta, producto['id_producto'], tipo, cantidad, producto['precio']))

            # Actualizar stock
            cursor.execute("UPDATE inventario SET stock = stock - %s WHERE id_producto = %s", (cantidad, producto['id_producto']))

            conn.commit()
            messagebox.showinfo("Venta exitosa", f"Venta registrada por ${total:.2f}")
            venta.destroy()

        except ValueError:
            messagebox.showerror("Error", "Debes ingresar números válidos.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def cancelar():
        respuesta = messagebox.askyesno("Cancelar", "¿Está seguro que quiere cancelar?")
        if respuesta:
            venta.destroy()

    # Botón para confirmar venta
    tk.Button(venta, text="Confirmar Venta", command=confirmar).pack(pady=10)

    # Botón para cancelar venta
    tk.Button(venta, text="Cancelar", command=cancelar).pack(pady=10)

    venta.mainloop()
    conn.close()

# ---------------- CONSULTAR INVENTARIO ----------------
def consultar_inventario():
    conn = conectar_db()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)

    inventario = tk.Tk()
    inventario.title("Inventario Actual")
    inventario.geometry("500x400")

    tk.Label(inventario, text="Inventario de Productos", font=("Arial", 14)).pack(pady=10)

    cursor.execute("""
        SELECT producto.id_producto,
               COALESCE(libro.título, revista.titulo) AS nombre,
               COALESCE(libro.precio, revista.precio) AS precio,
               inventario.stock
        FROM producto
        LEFT JOIN libro ON producto.id_libro = libro.id_libro
        LEFT JOIN revista ON producto.id_revista = revista.id_revista
        JOIN inventario ON producto.id_producto = inventario.id_producto
    """)

    items = cursor.fetchall()

    for item in items:
        tk.Label(inventario, text=f"{item['nombre']} | Precio: ${item['precio']:.2f} | Stock: {item['stock']}").pack(anchor='w')

    inventario.mainloop()
    conn.close()

# ---------------- INICIO DE SESIÓN ----------------
mostrar_login()
