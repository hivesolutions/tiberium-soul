{% extends "partials/layout.html.tpl" %}
{% block header %}
    {{ super() }}
    <div class="links sub-links">
        {% if sub_link == "info" %}
            <a href="{{ url_for('show_app', id = app.id) }}" class="active">info</a>
        {% else %}
            <a href="{{ url_for('show_app', id = app.id) }}">info</a>
        {% endif %}
    </div>
{% endblock %}
