{% extends "partials/layout_app.html.tpl" %}
{% block title %}Apps{% endblock %}
{% block name %}Apps :: {{ app.name }}{% endblock %}
{% block content %}
    <table>
        <tbody>
            {% for key, value in app.env.items() %}
                <tr>
                    <td class="right label" width="50%">{{ key }}</td>
                    <td class="left value" width="50%">{{ value }}</td>
                </tr>
            {% endfor %}
        </tbody>
    </table>
{% endblock %}
