from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'SACHIN SHARMA Bot is Running 24/7'

if __name__ == "__main__":
    app.run()
  
