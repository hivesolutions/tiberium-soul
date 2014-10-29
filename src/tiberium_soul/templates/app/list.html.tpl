{% extends "partials/layout.html.tpl" %}
{% block title %}Apps{% endblock %}
{% block name %}Apps{% endblock %}
{% block content %}
    <ul>
        {% for app in apps %}
            <li>
                <div class="name">
                    <a href="{{ url_for('show_app', id = app.id) }}">{{ app.name }}</a>
                </div>
                <div class="description">
                    {{ app.description }}
                </div>
            </li>
        {% endfor %}
    </ul>
{% endblock %}
