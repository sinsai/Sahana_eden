/* http://wiki.openqa.org/display/SIDE/record+and+assert+Ext+JS */

Selenium.prototype.assertExtEqual = function(expression, text) {
	/**
	 * the euqal assertion of ext
	 * @param expression ext expression , just like "button1.text" or "text1.getValue()"
	 * @param String target value
	 */
	var result = this.extEval(expression)
	if (result != text) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is not equal with " + text);
	}
};

Selenium.prototype.assertExtGreaterThan = function(expression, text) {
	/**
	 * the greater than assertion of ext
	 * @param expression ext expression , just like "button1.text" or "text1.getValue()"
	 * @param String target value
	 */
	var result = this.extEval(expression)
	if (result <= text) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is not greater than " + text);
	}
}

Selenium.prototype.assertExtGreaterEqualThan = function(expression, text) {
	/**
	 * the greater and equal than assertion of ext
	 * @param expression ext expression , just like "button1.text" or "text1.getValue()"
	 * @param String target value
	 */
	var result = this.extEval(expression)
	if (result < text) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is not greater equal than " + text);
	}
}

Selenium.prototype.assertExtLessThan = function(expression, text) {
	/**
	 * the less than assertion of ext
	 * @param expression ext expression , just like "button1.text" or "text1.getValue()"
	 * @param String target value
	 */
	var result = this.extEval(expression)
	if (result >= text) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is not less than " + text);
	}
}

Selenium.prototype.assertExtLessEqualThan = function(expression, text) {
	/**
	 * the less and equal than assertion of ext
	 * @param expression ext expression , just like "button1.text" or "text1.getValue()"
	 * @param String target value
	 */
	var result = this.extEval(expression)
	if (result > text) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is not less equal than " + text);
	}
}

Selenium.prototype.doExecuteExtFunction = function(expression, text) {
	/**
	 * do ext function ,if the expression end with ")" ,the params is not useful
	 * @param expression ext expression return a ext function, just like "button1.getText" or "text1.getValue()"
	 * @param String params ,just like "a,b,c"
	 */
	if (expression.lastIndexOf(")") == expression.length - 1) {
		this.extEval(expression);
	} else {
		var scopeObj = this.extEval(expression.substring(0, expression
				.lastIndexOf(".")));
		var func = this.extEval(expression);
		if (typeof(func) != "function") {
			Assert.fail("the value of [" + func + "] " + expression
					+ " is not a function");
		}
		var params = [];
		if (text) {
			params = text.split(",");
		}
		try {
			func.apply(scopeObj, params);
		} catch (e) {
			Assert.fail("error execute function [" + func + "] " + expression);
		}
	}
}

Selenium.prototype.assertExtTrue = function(expression) {
	/**
	 * the true assertion of ext
	 * @param expression ext expression , just like "button1.hidden"
	 */
	var result = this.extEval(expression);
	if (result !== true) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is not true");
	}
}

Selenium.prototype.assertExtFalse = function(expression) {
	/**
	 * the false assertion of ext
	 * @param expression ext expression , just like "button1.hidden"
	 */
	var result = this.extEval(expression);
	if (result !== true) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is not false");
	}
}


Selenium.prototype.assertExtNull = function(expression, text) {
	/**
	 * the null assertion of ext
	 * @param expression ext expression , just like "button1.text"
	 */
	var result = this.extEval(expression);
	if (result !== null) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is not null");
	}
}


Selenium.prototype.assertExtNotNull = function(expression, text) {
	/**
	 * the not null assertion of ext
	 * @param expression ext expression , just like "button1.text"
	 */
	var result = this.extEval(expression);
	if (result === null) {
		Assert.fail("the value of [" + result + "] " + expression + " is null");
	}
}


Selenium.prototype.assertExtUndefined = function(expression, text) {
	/**
	 * the undefined assertion of ext
	 * @param expression ext expression , just like "button1"
	 */
	var result = this.extEval(expression);
	if (result !== undefined) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is not undefined");
	}
}


Selenium.prototype.assertExtNotUndefined = function(expression, text) {
	/**
	 * the not undefined assertion of ext
	 * @param expression ext expression , just like "button1"
	 */
	var result = this.extEval(expression);
	if (result === undefined) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is undefined");
	}
}


Selenium.prototype.assertExtPresent = function(expression, text) {
	/**
	 * the present assertion of ext
	 * @param expression ext expression , just like "button1"
	 */
	var result = this.extEval(expression);
	if (result == null || result == undefined) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is not present");
	}
}

Selenium.prototype.assertExtNotPresent = function(expression, text) {
	/**
	 * the not present assertion of ext
	 * @param expression ext expression , just like "button1"
	 */
	var result = this.extEval(expression);
	if (result != null || result != undefined) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is present");
	}
}

Selenium.prototype.assertExtMatches = function(expression, text) {
	/**
	 * the matches assertion of ext
	 * @param expression ext expression , just like "button1.text" or "text1.getValue()"
	 * @param String target value
	 */
	var result = this.extEval(expression);
	var reg = new RegExp(text);
	if (!reg.test(result)) {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is not match " + text);
	}
}

Selenium.prototype.assertExtContains = function(expression, text) {
	/**
	 * the contains assertion of ext
	 * @param expression ext expression , just like "button1.text" or "text1.getValue()"
	 * @param String target value
	 */
	var result = this.extEval(expression);
	if (typeof(result) == "undefined" || result == null) {
		Assert.fail("the value of " + expression + " dos not contains " + text);
	} else if (result.indexOf) {
		if (result.indexOf(text) < 0) {
			Assert.fail("the value of [" + result + "] " + expression
					+ " dos not contains " + text);
		}
	} else {
		Assert.fail("the value of [" + result + "] " + expression
				+ " is not a String or Array");
	}
}

Selenium.prototype.assertExtTypeof = function(expression, text) {
	/**
	 * the typeof assertion of ext
	 * @param expression ext expression , just like "button1.text" or "text1.getValue()"
	 * @param String target value
	 */
	var type = typeof(this.extEval(expression));
	if (type != text) {
		Assert.fail("the type of [" + type + "] " + expression + " is not "
				+ text);
	}
}

PageBot.prototype.getWrappedWindow = function(extpath) {
	var win = this.getCurrentWindow() || {};
	return win.wrappedJSObject;
}


Selenium.prototype.getWrappedWindow = function(extpath) {
	return this.browserbot.getWrappedWindow();
}


Selenium.prototype.extEval = function(expression) {
	var script = expression;
	if (expression) {
		var expArr = expression.split(".");
		expArr[0] = "(window.Ext.getCmp('" + expArr[0] + "')||window.Ext.get('"
				+ expArr[0] + "')||window.Ext.StoreMgr.lookup('" + expArr[0]
				+ "'))";
		expression = expArr.join(".");
	}
	try {
		return this.doEval(expression);
	} catch (e) {
		throw new SeleniumError("the expression " + script
				+ " is not a Ext expression !");
	}
};
// I have to rewrite the eval function to get the context of window
Selenium.prototype.doEval = function(expression) {
	/**
	 * execute js ecpression
	 *
	 * @param {Object}
	 *            expression js expression
	 */
	try {
		var win = this.getWrappedWindow();
		var result = eval(expression, win);
		return result;
	} catch (e) {
		throw new SeleniumError("the expression " + expression
				+ " is not a Ext expression !");
	}
}
