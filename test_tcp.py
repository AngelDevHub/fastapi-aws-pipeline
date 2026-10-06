import socket

def send_tcp_message(host, message):
    port = 6061
    print(f"Conectando a {host}:{port}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5) # 5 segundos de espera
        s.connect((host, port))
        
        # Enviamos el mensaje
        s.sendall(message.encode('utf-8'))
        
        # Recibimos la respuesta
        data = s.recv(2048) # Aumentamos el buffer por si la DB ya tiene muchos registros
        print(f"✅ Enviado: {message}")
        print(f"📥 Recibido del Servidor: {data.decode('utf-8')}\n")
        s.close()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("(Verifica que el Security Group en AWS tenga el puerto 6061 abierto para 0.0.0.0/0)")

if __name__ == '__main__':
    print("=== PRUEBA DE CONEXIÓN TCP (PRÁCTICA 2) ===")
    ec2_ip = input("Por favor, ingresa la IP Pública de tu EC2 en AWS: ").strip()
    
    if ec2_ip:
        print("\n--- Iniciando Pruebas TCP ---")
        # Prueba 1: Insertar un autor
        insert_msg = '{"table": "authors", "data": {"name": "Autor Remoto desde mi PC"}}'
        send_tcp_message(ec2_ip, f'{{insert:{insert_msg}}}')
        
        # Prueba 2: Leer todos los autores
        get_msg = '{"table": "authors"}'
        send_tcp_message(ec2_ip, f'{{get:{get_msg}}}')
    else:
        print("Debes ingresar una IP válida para hacer la prueba.")
