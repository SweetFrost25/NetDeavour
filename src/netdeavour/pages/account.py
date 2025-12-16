from dash import html, dcc, register_page, callback, Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask import session
import dash_ag_grid as dag
from datetime import datetime
import dash

from netdeavour.auth import get_user_by_id, get_all_users, create_user_by_admin, delete_user, toggle_user_block


register_page(__name__, path="/account")


def layout(**kwargs):
	user_id = session.get("user_id")
	if not user_id:
		return html.Div(
			[
				html.H2("Account"),
				html.P("You are not logged in."),
				dcc.Link("Go to login page", href="/login"),
			],
			className="account-container",
		)

	user = get_user_by_id(user_id)
	if not user:
		return html.Div(
			[
				html.H2("Account"),
				html.P("User not found."),
				dcc.Link("Go to login page", href="/login"),
			],
			className="account-container",
		)

	is_admin = user.get("is_admin", False) or session.get("is_admin", False)

	# Особиста інформація
	account_info = html.Div(
		[
			html.H3("My Account"),
			html.P(f"Username: {user['username']}"),
			html.P(f"Created: {datetime.fromtimestamp(user['created_at']).strftime('%Y-%m-%d %H:%M:%S')}"),
			html.P(f"Role: {'Administrator' if is_admin else 'User'}"),
			dbc.Button("Logout", id="btn-logout", color="danger", class_name="mt-3"),
		],
		className="account-info-section",
	)

	# Адмін-панель - завжди створюємо елементи, але показуємо тільки для адмінів
	admin_panel = html.Div(
		[
			html.Hr(),
			html.H3("User Management"),
			html.Div(
				[
					dbc.Label("New Username", html_for="admin-new-username"),
					dcc.Input(
						id="admin-new-username",
						type="text",
						className="admin-input",
						placeholder="Enter username",
					),
					dbc.Label("New Password", html_for="admin-new-password", class_name="mt-2"),
					dcc.Input(
						id="admin-new-password",
						type="password",
						className="admin-input",
						placeholder="Enter password",
					),
					dbc.Button(
						"Create User",
						id="btn-create-user",
						color="success",
						class_name="mt-3",
						n_clicks=0,
					),
					html.Div(id="admin-message", className="admin-message mt-3"),
				],
				className="admin-create-section",
				style={"display": "none" if not is_admin else "block"},
			),
			html.Hr(style={"display": "none" if not is_admin else "block"}),
			html.H4("All Users", style={"display": "none" if not is_admin else "block"}),
			html.Div(id="admin-users-list", className="admin-users-list"),
		],
		className="admin-panel-section",
		style={"display": "none" if not is_admin else "block"},
	)

	return html.Div(
		[
			dcc.Location(id="account-redirect", refresh=True),
			dcc.Store(id="admin-users-store", data=[]),
			account_info,
			admin_panel,
		],
		className="account-container",
	)


@callback(
	Output("account-redirect", "pathname"),
	Input("btn-logout", "n_clicks"),
	prevent_initial_call=True,
)
def logout(n_clicks):
	if not n_clicks:
		raise PreventUpdate
	# Очистити сесію
	session.clear()
	return "/login"


@callback(
	Output("admin-users-store", "data", allow_duplicate=True),
	Input("admin-users-store", "data"),
	prevent_initial_call='initial_duplicate',
)
def load_users_list(current_data):
	user_id = session.get("user_id")
	if not user_id:
		return []
	
	user = get_user_by_id(user_id)
	if not user or not user.get("is_admin", False):
		return []
	
	users = get_all_users()
	formatted_users = []
	
	for u in users:
		formatted_users.append({
			"id": u["id"],
			"username": u["username"],
			"is_admin": u["is_admin"],
			"is_blocked": u["is_blocked"],
			"created_at": u["created_at"],
		})
	
	return formatted_users


@callback(
	Output("admin-users-list", "children", allow_duplicate=True),
	Input("admin-users-store", "data"),
	prevent_initial_call='initial_duplicate',
)
def render_users_list(users_data):
	user_id = session.get("user_id")
	if not user_id:
		return html.Div()
	
	user = get_user_by_id(user_id)
	if not user or not user.get("is_admin", False):
		return html.Div()
	
	if not users_data:
		return html.Div()
	
	# Створюємо список користувачів з кнопками
	user_cards = []
	for u in users_data:
		user_cards.append(
			dbc.Card(
				[
					dbc.CardBody(
						[
							html.H5(u["username"], className="card-title"),
							html.P(f"ID: {u['id']}"),
							html.P(f"Admin: {'Yes' if u['is_admin'] else 'No'}"),
							html.P(f"Blocked: {'Yes' if u['is_blocked'] else 'No'}"),
							html.P(f"Created: {datetime.fromtimestamp(u['created_at']).strftime('%Y-%m-%d %H:%M:%S')}"),
							html.Div(
								[
									dbc.Button(
										"Block/Unblock" if not u["is_blocked"] else "Unblock",
										id={"type": "admin-block-btn", "user_id": u["id"]},
										color="warning" if not u["is_blocked"] else "success",
										class_name="me-2",
										n_clicks=0,
									),
									dbc.Button(
										"Delete",
										id={"type": "admin-delete-btn", "user_id": u["id"]},
										color="danger",
										n_clicks=0,
										disabled=(u["id"] == user_id),  # Не можна видалити себе
									),
								],
								className="mt-2",
							),
						]
					)
				],
				className="mb-3",
			)
		)
	
	return html.Div(user_cards)


@callback(
	Output("admin-message", "children"),
	Output("admin-new-username", "value"),
	Output("admin-new-password", "value"),
	Output("admin-users-store", "data", allow_duplicate=True),
	Input("btn-create-user", "n_clicks"),
	State("admin-new-username", "value"),
	State("admin-new-password", "value"),
	prevent_initial_call=True,
)
def create_user(n_clicks, username, password):
	if not n_clicks:
		raise PreventUpdate
	
	user_id = session.get("user_id")
	if not user_id:
		return "You are not logged in.", "", "", []
	
	user = get_user_by_id(user_id)
	if not user or not user.get("is_admin", False):
		return "Access denied.", "", "", []
	
	if not username or not password:
		return "Please provide username and password.", username or "", password or "", []
	
	try:
		create_user_by_admin(username.strip(), password)
		# Оновлюємо список користувачів
		users = get_all_users()
		formatted_users = []
		for u in users:
			formatted_users.append({
				"id": u["id"],
				"username": u["username"],
				"is_admin": u["is_admin"],
				"is_blocked": u["is_blocked"],
				"created_at": u["created_at"],
			})
		return f"User '{username}' created successfully.", "", "", formatted_users
	except Exception as e:
		return f"Error: {str(e)}", username or "", password or "", []


@callback(
	Output("admin-users-store", "data", allow_duplicate=True),
	Input({"type": "admin-block-btn", "user_id": ALL}, "n_clicks"),
	prevent_initial_call=True,
)
def handle_block_user(block_clicks):
	
	user_id = session.get("user_id")
	if not user_id:
		return []
	
	user = get_user_by_id(user_id)
	if not user or not user.get("is_admin", False):
		return []
	
	ctx = dash.callback_context
	if not ctx.triggered:
		raise PreventUpdate
	
	triggered = ctx.triggered[0]
	triggered_id = triggered["prop_id"]
	
	# Парсимо user_id з triggered_id
	import json
	try:
		id_str = triggered_id.split(".n_clicks")[0]
		btn_data = json.loads(id_str)
		target_user_id = btn_data.get("user_id")
		
		if target_user_id and target_user_id != user_id:  # Не можна заблокувати себе
			toggle_user_block(target_user_id)
	except Exception as e:
		print(f"[!] Error blocking user: {e}")
	
	# Оновлюємо список
	users = get_all_users()
	formatted_users = []
	for u in users:
		formatted_users.append({
			"id": u["id"],
			"username": u["username"],
			"is_admin": u["is_admin"],
			"is_blocked": u["is_blocked"],
			"created_at": u["created_at"],
		})
	
	return formatted_users


@callback(
	Output("admin-users-store", "data", allow_duplicate=True),
	Input({"type": "admin-delete-btn", "user_id": ALL}, "n_clicks"),
	prevent_initial_call=True,
)
def handle_delete_user(delete_clicks):
	
	user_id = session.get("user_id")
	if not user_id:
		return []
	
	user = get_user_by_id(user_id)
	if not user or not user.get("is_admin", False):
		return []
	
	ctx = dash.callback_context
	if not ctx.triggered:
		raise PreventUpdate
	
	triggered = ctx.triggered[0]
	triggered_id = triggered["prop_id"]
	
	# Парсимо user_id з triggered_id
	import json
	try:
		id_str = triggered_id.split(".n_clicks")[0]
		btn_data = json.loads(id_str)
		target_user_id = btn_data.get("user_id")
		
		if target_user_id and target_user_id != user_id:  # Не можна видалити себе
			delete_user(target_user_id)
	except Exception as e:
		print(f"[!] Error deleting user: {e}")
	
	# Оновлюємо список
	users = get_all_users()
	formatted_users = []
	for u in users:
		formatted_users.append({
			"id": u["id"],
			"username": u["username"],
			"is_admin": u["is_admin"],
			"is_blocked": u["is_blocked"],
			"created_at": u["created_at"],
		})
	
	return formatted_users
