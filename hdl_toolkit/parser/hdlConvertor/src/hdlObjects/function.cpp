#include "function.h"

Function::Function(
		char * name,
		bool isOperator,
		Expr * returnT,
		std::vector<Variable> * params) {
	this->name = name;
	this->isOperator = isOperator;
	this->returnT = returnT;
	this->params = params;
}

PyObject * Function::toJson() const {
	PyObject *d = Named::toJson();
	PyDict_SetItemString(d, "isOperator", PyBool_FromLong(isOperator));
	if (!returnT) {
		PyDict_SetItemString(d, "returnT", returnT->toJson());
	} else {
		Py_IncRef(Py_None);
		PyDict_SetItemString(d, "returnT", Py_None);
		addJsonArr(d, "params", *params);
		addJsonArr(d, "locals", locals);
		addJsonArr(d, "body", body);
	}
	return d;
}