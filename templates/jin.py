
from jinja2 import Environment, FileSystemLoader

file_loader = FileSystemLoader('templates')

env = Environment(loader=file_loader)
template = env.get_template('zin.jinja2')
print(template.render(name="Mary", animal="lamb"))
