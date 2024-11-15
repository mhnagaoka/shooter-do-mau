# This is actually a template file, which will be replaced by a GitHub action
# See https://github.com/chuhlomin/render-template
def build_info() -> str:
    return "{{.build_info}}" if ".build_info" not in "{{.build_info}}" else "local dev"
