from django import template
from hrms.utils import decision_apps_to_context, decision_map_to_context
from hrms.models import WageClass, RankClass

register = template.Library()

@register.inclusion_tag("hrms/partials/timeline.html")
def render_decision_timeline(decision):
    return decision_apps_to_context(decision)

@register.inclusion_tag("hrms/partials/timeline.html")
def render_map_timeline(map):
    return decision_map_to_context(map)

@register.inclusion_tag("hrms/partials/wageclass.html")
def render_wageclass(wageclass):
    wageclass_info = wageclass.info()
    return wageclass_info

@register.inclusion_tag("hrms/partials/rankclass.html")
def render_rankclass(rankclass):
    return rankclass.info()

@register.inclusion_tag("hrms/partials/experience.html")
def render_experience(experience):
    return experience



