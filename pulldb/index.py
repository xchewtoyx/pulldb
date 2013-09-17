from pulldb.base import BaseHandler

class MainPage(BaseHandler):
  def get(self):
    template_values = {
    }
    template_values.update(self.get_user_info())
    template = self.templates.get_template('index.html')
    self.response.write(template.render(template_values))
