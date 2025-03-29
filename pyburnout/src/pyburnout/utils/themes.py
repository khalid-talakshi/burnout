def apply_burnout_style(plot):
  plot.update_layout(
      plot_bgcolor="#2D2D2D",
      paper_bgcolor="#2D2D2D",
      font_color="white",
      title_font_family="Old Car",
      title_font_size=24,
  )
  plot.update_xaxes(title_font_family="Old Car", title_font_size=18)
  plot.update_yaxes(title_font_family="Old Car", title_font_size=18)