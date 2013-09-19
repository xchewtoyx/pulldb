from pulldb.base import BaseHandler

class MainPage(BaseHandler):
  def get(self):
    template_values = self.base_template_values()
    template = self.templates.get_template('index.html')
    self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
