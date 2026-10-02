import os

# pytest carica questo file prima di tests/conftest.py e prima di ogni test: è l'unico posto in cui
# l'ambiente si imposta in tempo, perché Settings si costruisce all'import di src e legge l'ambiente
# in quel momento. Una variabile d'ambiente vince sul .env.
os.environ["JWT_SECRET"] = "segreto-dei-test-che-non-firma-niente-di-vero"
# Dal Giorno 9: chiavi finte, anche qui senza setdefault. La tua chiave vera sta nel .env, e un test
# che dimentica il suo finto la userebbe: con questa riceve un 401, che si vede, invece di una
# fattura, che no. Deve stare qui in cima, prima che l'import di src costruisca Settings.
os.environ["OPENAI_API_KEY"] = "sk-test-mai-valida"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-mai-valida"
# il modello di default di questo progetto passa da opencode: la stessa ragione, la sua chiave
os.environ["OPENCODE_API_KEY"] = "sk-opencode-test-mai-valida"
# Dal Giorno 10: i test hanno un database loro. Quelli del Giorno 9 e 10 fanno TRUNCATE di utenti,
# conti e documenti, e il database del .env è anche quello del compose: lo svuoterebbero. La CI
# lo indica con TEST_DATABASE_URL; in locale è lipari_ai_test, nello stesso Postgres. Le
# migrazioni non partono da sole: dopo una migrazione nuova, una volta anche qui, con
#   $env:DATABASE_URL = "postgresql+asyncpg://lipari:lipari@localhost:5432/lipari_ai_test"
#   uv run alembic upgrade head
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://lipari:lipari@localhost:5432/lipari_ai_test"
)
# e niente Redis, anche se il .env un giorno ce l'avrà: nei test la cache è quella di fakeredis
os.environ["REDIS_URL"] = ""
