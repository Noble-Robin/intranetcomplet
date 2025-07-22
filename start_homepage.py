#!/usr/bin/env python
import http.server
import socketserver
import webbrowser
import threading
import time

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=".", **kwargs)

def start_server():
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🚀 Serveur de la page d'accueil démarré sur http://localhost:{PORT}")
        print("📱 Ouvrez votre navigateur à cette adresse")
        print("🔄 Pour arrêter le serveur, appuyez sur Ctrl+C")
        
        # Ouvrir automatiquement le navigateur après 1 seconde
        def open_browser():
            time.sleep(1)
            webbrowser.open(f'http://localhost:{PORT}')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Serveur arrêté")
            httpd.shutdown()

if __name__ == "__main__":
    start_server()
