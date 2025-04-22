import streamlit as st
import streamlit.components.v1 as components

components.html(
    """
    <html>
      <head>
        <script>
          document.write("JavaScript está rodando!");
        </script>
        <noscript>
          Você precisa ativar o JavaScript para rodar este app.
        </noscript>
      </head>
      <body></body>
    </html>
    """,
    height=100
)