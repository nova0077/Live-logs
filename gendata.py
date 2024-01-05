import time

file_path = "debug.log"
i = 0

def append_random_string_to_file():
    global i
    with open(file_path, "a") as file:
        file.write("abcdef" + str(i) + " \n")
        file.write("\n")
        i += 1
        print("Random string appended to debug.log")

# Run the function every 3 seconds
while True:
    append_random_string_to_file()
    time.sleep(1)
