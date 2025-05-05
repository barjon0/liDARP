with open("model.lp", "r+") as file:
    content = file.read()

    file.seek(0)
    file.write(content.replace("#","_"))
    file.close()
