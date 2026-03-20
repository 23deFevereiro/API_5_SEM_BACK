from ..models.demo import Demo
def get_demo():
	return list(Demo.objects.all().values())