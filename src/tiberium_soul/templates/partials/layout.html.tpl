{% include "partials/doctype.html.tpl" %}
<head>
    {% block head %}
        {% include "partials/content_type.html.tpl" %}
        {% include "partials/includes.html.tpl" %}
        <title>Tiberium / {% block title %}{% endblock %}</title>
    {% endblock %}
</head>
<body class="ux romantic">
    <div id="header">
        {% block header %}
            <h1>{% block name %}{% endblock %}</h1>
            <div class="links">
                {% if link == "home" %}
                    <a href="{{ url_for('index') }}" class="active">home</a>
                {% else %}
                    <a href="{{ url_for('index') }}">home</a>
                {% endif %}
                //
                {% if link == "apps" %}
                    <a href="{{ url_for('list_app') }}" class="active">apps</a>
                {% else %}
                    <a href="{{ url_for('list_app') }}">apps</a>
                {% endif %}
                //
                {% if link == "new_app" %}
                    <a href="{{ url_for('new_app') }}" class="active">new app</a>
                {% else %}
                    <a href="{{ url_for('new_app') }}">new app</a>
                {% endif %}
                //
                {% if link == "about" %}
                    <a href="{{ url_for('about') }}" class="active">about</a>
                {% else %}
                    <a href="{{ url_for('about') }}">about</a>
                {% endif %}
            </div>
        {% endblock %}
    </div>
    <div id="content">{% block content %}{% endblock %}</div>
    {% include "partials/footer.html.tpl" %}
</body>
{% include "partials/end_doctype.html.tpl" %}
