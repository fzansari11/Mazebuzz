from maze import app

if __name__ == "__main__":
    #context = ('/etc/apache2/ssl/apache.crt', '/etc/apache2/ssl/apache.key')
    #app.run(host='0.0.0.0', port=5000, ssl_context=context, threaded=True, debug=True)
    app.run(host='0.0.0.0', debug=True)
    
