import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry
import psycopg2
from datetime import datetime
import pytz
import random
from Administrar_Agendamento import abrir_tela_suas_reunioes

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DB_NAME = "nome_do_banco"
DB_USER = "usuario"
DB_PASSWORD = "senha"
DB_HOST = "host"
DB_PORT = "porta"

FUSO_BRASILIA = "%d/%m/%Y %H:%M"
tz_brasilia = pytz.timezone('America/Sao_Paulo')

disponibilidade = [f"{h:02d}:{m:02d}" for h in range(7, 18) for m in (0, 30) if not (h == 17 and m == 30)]

def conectar_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def gerar_id():
    with conectar_db() as conn:
        cursor = conn.cursor()
        while True:
            id_aleatorio = random.randint(10000, 99999)
            cursor.execute("SELECT 1 FROM reservas WHERE id = %s", (id_aleatorio,))
            if not cursor.fetchone():
                return id_aleatorio

def criar_tabela():
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                data DATE NOT NULL,
                inicio TIME NOT NULL,
                fim TIME NOT NULL,
                bebida TEXT,
                inicio_completo TIMESTAMP NOT NULL,
                fim_completo TIMESTAMP NOT NULL
            )
        """)
        conn.commit()

def carregar_reservas():
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, data, inicio, fim, bebida FROM reservas ORDER BY data, inicio")
        return cursor.fetchall()

def salvar_reserva(reserva):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reservas (id, nome, data, inicio, fim, bebida, inicio_completo, fim_completo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            reserva["id"],
            reserva["nome"],
            reserva["data"],
            reserva["inicio"],
            reserva["fim"],
            reserva["bebida"],
            reserva["inicio_completo"],
            reserva["fim_completo"]
        ))
        conn.commit()

def limpar_reservas_expiradas():
    agora = datetime.now(tz_brasilia).strftime(FUSO_BRASILIA)
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reservas WHERE fim_completo < %s", (agora,))
        conn.commit()

def atualizar_horarios_fim(*args):
    inicio = inicio_var.get()
    if not inicio:
        fim_menu.configure(values=[])
        fim_var.set("")
        return

    hora_inicio, minuto_inicio = map(int, inicio.split(":"))
    fim_options = ["17:30"] if (hora_inicio == 17 and minuto_inicio == 0) else [
        f"{h:02d}:{m:02d}" for h in range(hora_inicio, 18) for m in (0, 30) if (h > hora_inicio or m > minuto_inicio)
    ]
    fim_menu.configure(values=fim_options)
    fim_var.set(fim_options[0])

def verifica_conflito(data, inicio_completo, fim_completo):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM reservas
            WHERE data = %s
              AND ((%s < fim_completo AND %s > inicio_completo))
        """, (data, inicio_completo, fim_completo))
        count = cursor.fetchone()[0]
        return count > 0

def reservar():
    btn_reservar.configure(state=ctk.DISABLED)

    nome = nome_var.get().strip().lower()
    data = data_var.get()
    inicio = inicio_var.get()
    fim = fim_var.get()
    bebida = bebida_var.get()

    if not nome:
        messagebox.showwarning("Aviso!!", "Por favor, digite um nome.")
        btn_reservar.configure(state=ctk.NORMAL)
        return

    if not data or not inicio or not fim:
        messagebox.showwarning("Aviso!!", "Por favor, selecione uma data e horário válido.")
        btn_reservar.configure(state=ctk.NORMAL)
        return

    inicio_completo = f"{data} {inicio}"
    fim_completo = f"{data} {fim}"

    try:
        inicio_completo = tz_brasilia.localize(datetime.strptime(inicio_completo, "%d/%m/%Y %H:%M"))
        fim_completo = tz_brasilia.localize(datetime.strptime(fim_completo, "%d/%m/%Y %H:%M"))
    except ValueError:
        messagebox.showwarning("Aviso!!", "Formato de data ou horário inválido.")
        btn_reservar.configure(state=ctk.NORMAL)
        return

    agora = datetime.now(tz_brasilia)
    if inicio_completo < agora or fim_completo < agora:
        messagebox.showwarning("Aviso!!", "Não é possível agendar.")
        btn_reservar.configure(state=ctk.NORMAL)
        return

    if verifica_conflito(data, inicio_completo, fim_completo):
        messagebox.showerror("Erro", "Conflito de agendamento! Escolha outro horário.")
        btn_reservar.configure(state=ctk.NORMAL)
        return

    confirmar = messagebox.askyesno("Confirmação", f"Confirma o agendamento para {nome} em {data} de {inicio} até {fim}\nSolicitação: {bebida}")

    if confirmar:
        reserva = {
            "id": gerar_id(),
            "nome": nome,
            "data": data,
            "inicio": inicio,
            "fim": fim,
            "inicio_completo": inicio_completo.strftime(FUSO_BRASILIA),
            "fim_completo": fim_completo.strftime(FUSO_BRASILIA),
            "bebida": bebida
        }
        salvar_reserva(reserva)
        messagebox.showinfo("Sucesso", f"Reunião agendada!\nID da reserva: {reserva['id']}\nNome: {nome}\nData: {data}")
        atualizar_lista_reservas()

    btn_reservar.configure(state=ctk.NORMAL)

# Interface
criar_tabela()
limpar_reservas_expiradas()

root = ctk.CTk()
root.title("Reserva de Reunião")
root.geometry("500x640")

messagebox.showinfo("Aviso Importante", "Ao finalizar seu agendamento, anote o ID que aparece na tela de sucesso.\nEsse ID é necessário para confirmar o agendamento.\n\nRealize o agendamento com antecedência para evitar conflitos.")

def criar_label(texto):
    return ctk.CTkLabel(root, text=texto, font=("Arial", 12))

criar_label("Para quem será o agendamento? (Apenas Letras Minusculas)").pack(pady=(10, 2))
nome_var = ctk.StringVar()
ctk.CTkEntry(root, textvariable=nome_var).pack(pady=2)

criar_label("Selecione a data da reunião:").pack(pady=(10, 2))
data_var = ctk.StringVar()
data_picker = DateEntry(root, textvariable=data_var, date_pattern="dd/MM/yyyy")
data_picker.pack(pady=2)

criar_label("Selecione o horário de início:").pack(pady=(10, 2))
inicio_var = ctk.StringVar()
inicio_menu = ctk.CTkComboBox(root, variable=inicio_var, values=disponibilidade, command=atualizar_horarios_fim)
inicio_menu.pack(pady=2)

criar_label("Selecione o horário de término:").pack(pady=(10, 2))
fim_var = ctk.StringVar()
fim_menu = ctk.CTkComboBox(root, variable=fim_var, values=[])
fim_menu.pack(pady=2)

criar_label("Gostaria de solicitar água ou café?").pack(pady=(10, 2))
bebida_var = ctk.StringVar(value="Nenhum")
frame_bebidas = ctk.CTkFrame(root, fg_color="transparent")
frame_bebidas.pack()
for opcao in ["Café", "Água", "Água e café", "Nenhum"]:
    ctk.CTkRadioButton(frame_bebidas, text=opcao, variable=bebida_var, value=opcao).pack(side="left", padx=5)

btn_reservar = ctk.CTkButton(root, text="Confirmar Agendamento", command=reservar)
btn_reservar.pack(pady=15)

botao_suas_reunioes = ctk.CTkButton(
    root,
    text="Suas Reuniões",
    command=lambda: abrir_tela_suas_reunioes(root, "#1f6aa5", "white", atualizar_lista_reservas),
    fg_color="#1f6aa5",
    text_color="white",
    corner_radius=10
)
botao_suas_reunioes.place(relx=0.85, rely=0.05, anchor="ne", x=50, y=10)

criar_label("Listagem de Agendamentos").pack(pady=(10, 2))
lista_reservas = ctk.CTkTextbox(root, height=220, width=450)
lista_reservas.pack(pady=10)

def atualizar_lista_reservas():
    lista_reservas.delete("1.0", ctk.END)
    reservas = carregar_reservas()
    for reserva in reservas:
        lista_reservas.insert(ctk.END, f"Dia: {reserva[1].strftime('%d/%m/%Y')}\n")
        lista_reservas.insert(ctk.END, f"Horário: {reserva[2]} às {reserva[3]}\n\n")

atualizar_lista_reservas()

root.mainloop()