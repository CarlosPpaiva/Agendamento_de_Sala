import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime
import psycopg2
import pytz

DB_NAME = "agendamento"
DB_USER = "postgres"
DB_PASSWORD = "$up@2025"
DB_HOST = "10.6.53.254"
DB_PORT = "5432"
FUSO_BRASILIA = "%d/%m/%Y %H:%M"
tz_brasilia = pytz.timezone('America/Sao_Paulo')
disponibilidade = [f"{h:02d}:{m:02d}" for h in range(7, 18) for m in (0, 30) if not (h == 17 and m == 30)]

def conectar_db():
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )

def abrir_tela_suas_reunioes(root, cor_botao, cor_texto_botao, atualizar_callback):
    def buscar_reunioes():
        nome = nome_entry.get().strip().lower()

        if not nome:
            messagebox.showwarning("Aviso", "Digite seu nome para buscar.")
            return

        query = "SELECT id, data, inicio, fim, bebida FROM reservas WHERE LOWER(nome) = %s"
        params = [nome]

        with conectar_db() as conn:
            cur = conn.cursor()
            cur.execute(query, tuple(params))
            resultados = cur.fetchall()

        for row in tree.get_children():
            tree.delete(row)

        if not resultados:
            messagebox.showinfo("Informação", "Nenhum agendamento encontrado.")
            return

        for res in resultados:
            tree.insert("", "end", values=(res[0], res[1].strftime("%d/%m/%Y"), res[2], res[3], res[4]))

    def editar_agendamento():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um agendamento.")
            return

        values = tree.item(selected, "values")
        agendamento_id, data, inicio, fim, bebida = values
        atualizar_callback()

        def atualizar_fim(*args):
            try:
                h, m = map(int, inicio_var.get().split(":"))
                nova_hora = h
                novo_minuto = m + 30
                if novo_minuto >= 60:
                    nova_hora += 1
                    novo_minuto -= 60
                fim_var.set(f"{nova_hora:02d}:{novo_minuto:02d}")
            except:
                pass  # Evita erro se ainda não houver valor

        def salvar_alteracoes():
            nova_data = data_entry.get()
            novo_inicio = inicio_var.get()
            novo_fim = fim_var.get()
            nova_bebida = bebida_var.get()

            if not nova_data or not novo_inicio or not novo_fim:
                messagebox.showwarning("Aviso", "Preencha todos os campos.")
                return

            try:
                inicio_completo = tz_brasilia.localize(datetime.strptime(f"{nova_data} {novo_inicio}", "%d/%m/%Y %H:%M"))
                fim_completo = tz_brasilia.localize(datetime.strptime(f"{nova_data} {novo_fim}", "%d/%m/%Y %H:%M"))
            except ValueError:
                messagebox.showerror("Erro", "Data ou hora inválida.")
                return

            if fim_completo <= inicio_completo:
                messagebox.showwarning("Aviso", "O horário de fim deve ser maior que o de início.")
                return

            with conectar_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT COUNT(*) FROM reservas
                    WHERE id != %s AND (
                        %s < fim_completo AND %s > inicio_completo
                    )
                """, (agendamento_id, inicio_completo, fim_completo))
                conflito = cur.fetchone()[0]

            if conflito > 0:
                messagebox.showerror("Erro", "Conflito de agendamento! Escolha outro horário.")
                return

            confirmar = messagebox.askyesno("Confirmação", "Deseja realmente salvar as alterações?")
            if not confirmar:
                return

            with conectar_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE reservas
                    SET data = %s, inicio = %s, fim = %s, bebida = %s,
                        inicio_completo = %s, fim_completo = %s
                    WHERE id = %s
                """, (nova_data, novo_inicio, novo_fim, nova_bebida,
                      inicio_completo.strftime(FUSO_BRASILIA), fim_completo.strftime(FUSO_BRASILIA), agendamento_id))
                conn.commit()

            messagebox.showinfo("Sucesso", "Agendamento atualizado.")
            editar_tela.destroy()
            buscar_reunioes()
            atualizar_callback()

        editar_tela = ctk.CTkToplevel(root)
        editar_tela.title("Editar Agendamento")
        editar_tela.geometry("350x300")

        ctk.CTkLabel(editar_tela, text="Data:").pack()
        data_entry = DateEntry(editar_tela, date_pattern="dd/mm/yyyy", locale='pt_BR')
        data_entry.set_date(datetime.strptime(data, "%d/%m/%Y"))
        data_entry.pack()

        ctk.CTkLabel(editar_tela, text="Início:").pack()
        inicio_var = ctk.StringVar(value=inicio)
        inicio_menu = ctk.CTkOptionMenu(editar_tela, variable=inicio_var, values=disponibilidade)
        inicio_menu.pack()
        inicio_var.trace_add("write", atualizar_fim)

        ctk.CTkLabel(editar_tela, text="Fim:").pack()
        fim_var = ctk.StringVar(value=fim)
        ctk.CTkOptionMenu(editar_tela, variable=fim_var, values=disponibilidade).pack()

        ctk.CTkLabel(editar_tela, text="Bebida:").pack()
        bebida_var = ctk.StringVar(value=bebida)
        ctk.CTkEntry(editar_tela, textvariable=bebida_var).pack()

        ctk.CTkButton(editar_tela, text="Salvar", command=salvar_alteracoes,
                      fg_color=cor_botao, text_color=cor_texto_botao, corner_radius=10).pack(pady=10)

    def excluir_agendamento():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um agendamento.")
            return

        values = tree.item(selected, "values")
        agendamento_id = values[0]

        confirm = messagebox.askyesno("Confirmação", "Deseja realmente excluir este agendamento?")
        if not confirm:
            return

        with conectar_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM reservas WHERE id = %s", (agendamento_id,))
            conn.commit()

        messagebox.showinfo("Sucesso", "Agendamento excluído.")
        buscar_reunioes()
        atualizar_callback()

    janela = ctk.CTkToplevel(root)
    janela.title("Suas Reuniões")
    janela.geometry("600x480")

    ctk.CTkLabel(janela, text="Digite seu nome:").pack(pady=5)
    nome_entry = ctk.CTkEntry(janela)
    nome_entry.pack(pady=5)

    ctk.CTkButton(janela, text="Buscar", command=buscar_reunioes,
                  fg_color=cor_botao, text_color=cor_texto_botao, corner_radius=10).pack(pady=5)

    import tkinter.ttk as ttk
    columns = ("ID", "Data", "Início", "Fim", "Bebida")
    tree = ttk.Treeview(janela, columns=columns, show="headings", height=8)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100 if col == "ID" else 120)
    tree.pack(pady=10)

    btn_frame = ctk.CTkFrame(janela, fg_color="transparent")
    btn_frame.pack()

    ctk.CTkButton(btn_frame, text="Editar", command=editar_agendamento,
                  fg_color=cor_botao, text_color=cor_texto_botao, corner_radius=10).pack(side="left", padx=10)
    ctk.CTkButton(btn_frame, text="Excluir", command=excluir_agendamento,
                  fg_color=cor_botao, text_color=cor_texto_botao, corner_radius=10).pack(side="left", padx=10)