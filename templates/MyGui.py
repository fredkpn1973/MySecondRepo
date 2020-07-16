import PySimpleGUI as sg
import re


def startGui():
    sg.theme("LightBlue3")

    layout = [[sg.Text('Some text on Row 1')],
              [sg.Text('Enter something on Row 2'), sg.InputText()],
              [sg.Button('Ok'), sg.Button('Cancel')]]

    window = sg.Window('VLAN Search', layout)

    while True:

        event, values = window.read()
        # if values[0].isdigit():
        #     print('You entered ', values[0])
        # else:
        #     print("You must enter a number")
        if event == sg.WIN_CLOSED or event == 'Ok':
            break

    window.close()
    return values[0]


if __name__ == "__main__":

    print(startGui())
