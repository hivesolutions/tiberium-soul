{% extends "partials/layout_app.html.tpl" %}
{% block title %}Apps{% endblock %}
{% block name %}Apps :: {{ app.name }}{% endblock %}
{% block content %}
    <div class="quote">{{ app.description }}</div>
    <div class="separator-horizontal"></div>
    <table>
        <tbody>
            <tr>
                <td class="right label" width="50%">domain</td>
                <td class="left value" width="50%">
                    <a href="{{ app.schema }}://{{ app.domain }}">{{ app.domain }}</a>
                </td>
            </tr>
            <tr>
                <td class="right label" width="50%">git</td>
                <td class="left value" width="50%">
                    <a href="#">{{ app.git }}</a>
                </td>
            </tr>
        </tbody>
    </table>
{% endblock %}
