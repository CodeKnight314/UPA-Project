import os
import datetime
import dash
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output

class UPA_DashApp:
    def __init__(self, upa):
        self.upa = upa
        self.app = dash.Dash(__name__)
        self.initial_investment = self.upa.broker.portfolio_value
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self):
        self.app.layout = html.Div([
            html.H1("Universal Portfolio Algorithm Monitor"),
            html.Div(id="portfolio-value-header", style={'fontSize': 20, 'marginBottom': 20}),
            dcc.Graph(id="portfolio-value-graph"),
            html.H2("Trades Log"),
            dcc.Textarea(id="trades-log", style={'width': '100%', 'height': 200}),
            dcc.Interval(id="interval-update", interval=5000, n_intervals=0)  # Update every 5 seconds
        ])

    def setup_callbacks(self):
        @self.app.callback(
            [Output("portfolio-value-header", "children"),
             Output("portfolio-value-graph", "figure"),
             Output("trades-log", "value")],
            [Input("interval-update", "n_intervals")]
        )
        def update_dashboard(n_intervals):
            # Update Portfolio Value Header
            current_value = self.upa.broker.portfolio_value
            header_text = f"Portfolio Value: ${current_value:.2f}"

            # Update Portfolio Value Graph
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            times, values = self.get_portfolio_data()
            times.append(current_time)
            values.append(current_value)
            figure = {
                'data': [
                    go.Scatter(x=times, y=values, mode='lines', name='Portfolio Value'),
                    go.Scatter(x=times, y=[self.initial_investment] * len(times), mode='lines', name='Initial Investment', line={'dash': 'dash'})
                ],
                'layout': go.Layout(title='Portfolio Value Over Time', xaxis={'title': 'Time'}, yaxis={'title': 'Value'})
            }

            # Update Trades Log
            log_content = ""
            if os.path.isfile(self.upa.output_logs):
                with open(self.upa.output_logs, 'r') as f:
                    log_content = f.read()

            return header_text, figure, log_content

    def get_portfolio_data(self):
        # Placeholder for retrieving historical portfolio data
        return [], []

    def run(self):
        self.app.run_server(debug=True)