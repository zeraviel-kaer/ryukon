from ryukon.config import Config

class Database:
    host: str
    port: int

class AppConfig:
    database: Database

c: AppConfig = Config("tests/test.json", lang="ru")
# set
c.set("database.host", "bro")
print(c.get("database.host"))        # newhost