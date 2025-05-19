import mysql.connector # type: ignore

def get_db_connection():
    connection = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='', 
        database='bd_software'
    )
    return connection

'''
## Banco de dados ##
CREATE TABLE resultados_placas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    caracteristica VARCHAR(10),
    data_processamento DATE,
    hora_processamento TIME,
    link_imagem TEXT(400)
);
'''