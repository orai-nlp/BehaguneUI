/*!
 * Clean Blog v1.0.0 (http://startbootstrap.com)
 * Copyright 2014 Start Bootstrap
 * Licensed under Apache 2.0 (https://github.com/IronSummitMedia/startbootstrap/blob/gh-pages/LICENSE)
 */

// Contact Form Scripts

$(function() {

    $("#contactFrom input,#contactForm textarea").jqBootstrapValidation({
        preventSubmit: true,
        submitError: function($form, event, errors) {
            // additional error messages or events
        },
        submitSuccess: function($form, event) {
            event.preventDefault(); // prevent default submit behaviour
            // get values from FORM
            var name = $("input#name").val();
            var email = $("input#email").val();
            var phone = $("input#phone").val();
            var message = $("textarea#message").val();
            var firstName = name; // For Success/Failure Message
            // Check for white space in name for Success/Fail message
            if (firstName.indexOf(' ') >= 0) {
                firstName = name.split(' ').slice(0, -1).join(' ');
            }
            $.ajax({
                url: "././mail/contact_me.php",
                type: "POST",
                data: {
                    name: name,
                    phone: phone,
                    email: email,
                    message: message
                },
                cache: false,
                success: function() {
                    // Success message
                    $('#success').html("<div class='alert alert-success'>");
                    $('#success > .alert-success').html("<button type='button' class='close' data-dismiss='alert' aria-hidden='true'>&times;")
                        .append("</button>");
                    $('#success > .alert-success')
                        .append("<strong>Your message has been sent. </strong>");
                    $('#success > .alert-success')
                        .append('</div>');

                    //clear all fields
                    $('#contactForm').trigger("reset");
                },
                error: function() {
                    // Fail message
                    $('#success').html("<div class='alert alert-danger'>");
                    $('#success > .alert-danger').html("<button type='button' class='close' data-dismiss='alert' aria-hidden='true'>&times;")
                        .append("</button>");
                    $('#success > .alert-danger').append("<strong>Sorry " + firstName + ", it seems that my mail server is not responding. Please try again later!");
                    $('#success > .alert-danger').append('</div>');
                    //clear all fields
                    $('#contactForm').trigger("reset");
                },
            })
        },
        filter: function() {
            return $(this).is(":visible");
        },
    });

    $("a[data-toggle=\"tab\"]").click(function(e) {
        e.preventDefault();
        $(this).tab("show");
    });
});


/*When clicking on Full hide fail/success boxes */
$('#name').focus(function() {
    $('#success').html('');
});

 // jqBootstrapValidation
 // * A plugin for automating validation on Twitter Bootstrap formatted forms.
 // *
 // * v1.3.6
 // *
 // * License: MIT <http://opensource.org/licenses/mit-license.php> - see LICENSE file
 // *
 // * http://ReactiveRaven.github.com/jqBootstrapValidation/
 

(function( $ ){

	var createdElements = [];

	var defaults = {
		options: {
			prependExistingHelpBlock: false,
			sniffHtml: true, // sniff for 'required', 'maxlength', etc
			preventSubmit: true, // stop the form submit event from firing if validation fails
			submitError: false, // function called if there is an error when trying to submit
			submitSuccess: false, // function called just before a successful submit event is sent to the server
            semanticallyStrict: false, // set to true to tidy up generated HTML output
			autoAdd: {
				helpBlocks: true
			},
            filter: function () {
                // return $(this).is(":visible"); // only validate elements you can see
                return true; // validate everything
            }
		},
    methods: {
      init : function( options ) {

        var settings = $.extend(true, {}, defaults);

        settings.options = $.extend(true, settings.options, options);

        var $siblingElements = this;

        var uniqueForms = $.unique(
          $siblingElements.map( function () {
            return $(this).parents("form")[0];
          }).toArray()
        );

        $(uniqueForms).bind("submit", function (e) {
          var $form = $(this);
          var warningsFound = 0;
          var $inputs = $form.find("input,textarea,select").not("[type=submit],[type=image]").filter(settings.options.filter);
          $inputs.trigger("submit.validation").trigger("validationLostFocus.validation");

          $inputs.each(function (i, el) {
            var $this = $(el),
              $controlGroup = $this.parents(".form-group").first();
            if (
              $controlGroup.hasClass("warning")
            ) {
              $controlGroup.removeClass("warning").addClass("error");
              warningsFound++;
            }
          });

          $inputs.trigger("validationLostFocus.validation");

          if (warningsFound) {
            if (settings.options.preventSubmit) {
              e.preventDefault();
            }
            $form.addClass("error");
            if ($.isFunction(settings.options.submitError)) {
              settings.options.submitError($form, e, $inputs.jqBootstrapValidation("collectErrors", true));
            }
          } else {
            $form.removeClass("error");
            if ($.isFunction(settings.options.submitSuccess)) {
              settings.options.submitSuccess($form, e);
            }
          }
        });

        return this.each(function(){

          // Get references to everything we're interested in
          var $this = $(this),
            $controlGroup = $this.parents(".form-group").first(),
            $helpBlock = $controlGroup.find(".help-block").first(),
            $form = $this.parents("form").first(),
            validatorNames = [];

          // create message container if not exists
          if (!$helpBlock.length && settings.options.autoAdd && settings.options.autoAdd.helpBlocks) {
              $helpBlock = $('<div class="help-block" />');
              $controlGroup.find('.controls').append($helpBlock);
							createdElements.push($helpBlock[0]);
          }

          // =============================================================
          //                                     SNIFF HTML FOR VALIDATORS
          // =============================================================

          // *snort sniff snuffle*

          if (settings.options.sniffHtml) {
            var message = "";
            // ---------------------------------------------------------
            //                                                   PATTERN
            // ---------------------------------------------------------
            if ($this.attr("pattern") !== undefined) {
              message = "Not in the expected format<!-- data-validation-pattern-message to override -->";
              if ($this.data("validationPatternMessage")) {
                message = $this.data("validationPatternMessage");
              }
              $this.data("validationPatternMessage", message);
              $this.data("validationPatternRegex", $this.attr("pattern"));
            }
            // ---------------------------------------------------------
            //                                                       MAX
            // ---------------------------------------------------------
            if ($this.attr("max") !== undefined || $this.attr("aria-valuemax") !== undefined) {
              var max = ($this.attr("max") !== undefined ? $this.attr("max") : $this.attr("aria-valuemax"));
              message = "Too high: Maximum of '" + max + "'<!-- data-validation-max-message to override -->";
              if ($this.data("validationMaxMessage")) {
                message = $this.data("validationMaxMessage");
              }
              $this.data("validationMaxMessage", message);
              $this.data("validationMaxMax", max);
            }
            // ---------------------------------------------------------
            //                                                       MIN
            // ---------------------------------------------------------
            if ($this.attr("min") !== undefined || $this.attr("aria-valuemin") !== undefined) {
              var min = ($this.attr("min") !== undefined ? $this.attr("min") : $this.attr("aria-valuemin"));
              message = "Too low: Minimum of '" + min + "'<!-- data-validation-min-message to override -->";
              if ($this.data("validationMinMessage")) {
                message = $this.data("validationMinMessage");
              }
              $this.data("validationMinMessage", message);
              $this.data("validationMinMin", min);
            }
            // ---------------------------------------------------------
            //                                                 MAXLENGTH
            // ---------------------------------------------------------
            if ($this.attr("maxlength") !== undefined) {
              message = "Too long: Maximum of '" + $this.attr("maxlength") + "' characters<!-- data-validation-maxlength-message to override -->";
              if ($this.data("validationMaxlengthMessage")) {
                message = $this.data("validationMaxlengthMessage");
              }
              $this.data("validationMaxlengthMessage", message);
              $this.data("validationMaxlengthMaxlength", $this.attr("maxlength"));
            }
            // ---------------------------------------------------------
            //                                                 MINLENGTH
            // ---------------------------------------------------------
            if ($this.attr("minlength") !== undefined) {
              message = "Too short: Minimum of '" + $this.attr("minlength") + "' characters<!-- data-validation-minlength-message to override -->";
              if ($this.data("validationMinlengthMessage")) {
                message = $this.data("validationMinlengthMessage");
              }
              $this.data("validationMinlengthMessage", message);
              $this.data("validationMinlengthMinlength", $this.attr("minlength"));
            }
            // ---------------------------------------------------------
            //                                                  REQUIRED
            // ---------------------------------------------------------
            if ($this.attr("required") !== undefined || $this.attr("aria-required") !== undefined) {
              message = settings.builtInValidators.required.message;
              if ($this.data("validationRequiredMessage")) {
                message = $this.data("validationRequiredMessage");
              }
              $this.data("validationRequiredMessage", message);
            }
            // ---------------------------------------------------------
            //                                                    NUMBER
            // ---------------------------------------------------------
            if ($this.attr("type") !== undefined && $this.attr("type").toLowerCase() === "number") {
              message = settings.builtInValidators.number.message;
              if ($this.data("validationNumberMessage")) {
                message = $this.data("validationNumberMessage");
              }
              $this.data("validationNumberMessage", message);
            }
            // ---------------------------------------------------------
            //                                                     EMAIL
            // ---------------------------------------------------------
            if ($this.attr("type") !== undefined && $this.attr("type").toLowerCase() === "email") {
              message = "Not a valid email address<!-- data-validator-validemail-message to override -->";
              if ($this.data("validationValidemailMessage")) {
                message = $this.data("validationValidemailMessage");
              } else if ($this.data("validationEmailMessage")) {
                message = $this.data("validationEmailMessage");
              }
              $this.data("validationValidemailMessage", message);
            }
            // ---------------------------------------------------------
            //                                                MINCHECKED
            // ---------------------------------------------------------
            if ($this.attr("minchecked") !== undefined) {
              message = "Not enough options checked; Minimum of '" + $this.attr("minchecked") + "' required<!-- data-validation-minchecked-message to override -->";
              if ($this.data("validationMincheckedMessage")) {
                message = $this.data("validationMincheckedMessage");
              }
              $this.data("validationMincheckedMessage", message);
              $this.data("validationMincheckedMinchecked", $this.attr("minchecked"));
            }
            // ---------------------------------------------------------
            //                                                MAXCHECKED
            // ---------------------------------------------------------
            if ($this.attr("maxchecked") !== undefined) {
              message = "Too many options checked; Maximum of '" + $this.attr("maxchecked") + "' required<!-- data-validation-maxchecked-message to override -->";
              if ($this.data("validationMaxcheckedMessage")) {
                message = $this.data("validationMaxcheckedMessage");
              }
              $this.data("validationMaxcheckedMessage", message);
              $this.data("validationMaxcheckedMaxchecked", $this.attr("maxchecked"));
            }
          }

          // =============================================================
          //                                       COLLECT VALIDATOR NAMES
          // =============================================================

          // Get named validators
          if ($this.data("validation") !== undefined) {
            validatorNames = $this.data("validation").split(",");
          }

          // Get extra ones defined on the element's data attributes
          $.each($this.data(), function (i, el) {
            var parts = i.replace(/([A-Z])/g, ",$1").split(",");
            if (parts[0] === "validation" && parts[1]) {
              validatorNames.push(parts[1]);
            }
          });

          // =============================================================
          //                                     NORMALISE VALIDATOR NAMES
          // =============================================================

          var validatorNamesToInspect = validatorNames;
          var newValidatorNamesToInspect = [];

          do // repeatedly expand 'shortcut' validators into their real validators
          {
            // Uppercase only the first letter of each name
            $.each(validatorNames, function (i, el) {
              validatorNames[i] = formatValidatorName(el);
            });

            // Remove duplicate validator names
            validatorNames = $.unique(validatorNames);

            // Pull out the new validator names from each shortcut
            newValidatorNamesToInspect = [];
            $.each(validatorNamesToInspect, function(i, el) {
              if ($this.data("validation" + el + "Shortcut") !== undefined) {
                // Are these custom validators?
                // Pull them out!
                $.each($this.data("validation" + el + "Shortcut").split(","), function(i2, el2) {
                  newValidatorNamesToInspect.push(el2);
                });
              } else if (settings.builtInValidators[el.toLowerCase()]) {
                // Is this a recognised built-in?
                // Pull it out!
                var validator = settings.builtInValidators[el.toLowerCase()];
                if (validator.type.toLowerCase() === "shortcut") {
                  $.each(validator.shortcut.split(","), function (i, el) {
                    el = formatValidatorName(el);
                    newValidatorNamesToInspect.push(el);
                    validatorNames.push(el);
                  });
                }
              }
            });

            validatorNamesToInspect = newValidatorNamesToInspect;

          } while (validatorNamesToInspect.length > 0)

          // =============================================================
          //                                       SET UP VALIDATOR ARRAYS
          // =============================================================

          var validators = {};

          $.each(validatorNames, function (i, el) {
            // Set up the 'override' message
            var message = $this.data("validation" + el + "Message");
            var hasOverrideMessage = (message !== undefined);
            var foundValidator = false;
            message =
              (
                message
                  ? message
                  : "'" + el + "' validation failed <!-- Add attribute 'data-validation-" + el.toLowerCase() + "-message' to input to change this message -->"
              )
            ;

            $.each(
              settings.validatorTypes,
              function (validatorType, validatorTemplate) {
                if (validators[validatorType] === undefined) {
                  validators[validatorType] = [];
                }
                if (!foundValidator && $this.data("validation" + el + formatValidatorName(validatorTemplate.name)) !== undefined) {
                  validators[validatorType].push(
                    $.extend(
                      true,
                      {
                        name: formatValidatorName(validatorTemplate.name),
                        message: message
                      },
                      validatorTemplate.init($this, el)
                    )
                  );
                  foundValidator = true;
                }
              }
            );

            if (!foundValidator && settings.builtInValidators[el.toLowerCase()]) {

              var validator = $.extend(true, {}, settings.builtInValidators[el.toLowerCase()]);
              if (hasOverrideMessage) {
                validator.message = message;
              }
              var validatorType = validator.type.toLowerCase();

              if (validatorType === "shortcut") {
                foundValidator = true;
              } else {
                $.each(
                  settings.validatorTypes,
                  function (validatorTemplateType, validatorTemplate) {
                    if (validators[validatorTemplateType] === undefined) {
                      validators[validatorTemplateType] = [];
                    }
                    if (!foundValidator && validatorType === validatorTemplateType.toLowerCase()) {
                      $this.data("validation" + el + formatValidatorName(validatorTemplate.name), validator[validatorTemplate.name.toLowerCase()]);
                      validators[validatorType].push(
                        $.extend(
                          validator,
                          validatorTemplate.init($this, el)
                        )
                      );
                      foundValidator = true;
                    }
                  }
                );
              }
            }

            if (! foundValidator) {
              $.error("Cannot find validation info for '" + el + "'");
            }
          });

          // =============================================================
          //                                         STORE FALLBACK VALUES
          // =============================================================

          $helpBlock.data(
            "original-contents",
            (
              $helpBlock.data("original-contents")
                ? $helpBlock.data("original-contents")
                : $helpBlock.html()
            )
          );

          $helpBlock.data(
            "original-role",
            (
              $helpBlock.data("original-role")
                ? $helpBlock.data("original-role")
                : $helpBlock.attr("role")
            )
          );

          $controlGroup.data(
            "original-classes",
            (
              $controlGroup.data("original-clases")
                ? $controlGroup.data("original-classes")
                : $controlGroup.attr("class")
            )
          );

          $this.data(
            "original-aria-invalid",
            (
              $this.data("original-aria-invalid")
                ? $this.data("original-aria-invalid")
                : $this.attr("aria-invalid")
            )
          );

          // =============================================================
          //                                                    VALIDATION
          // =============================================================

          $this.bind(
            "validation.validation",
            function (event, params) {

              var value = getValue($this);

              // Get a list of the errors to apply
              var errorsFound = [];

              $.each(validators, function (validatorType, validatorTypeArray) {
                if (value || value.length || (params && params.includeEmpty) || (!!settings.validatorTypes[validatorType].blockSubmit && params && !!params.submitting)) {
                  $.each(validatorTypeArray, function (i, validator) {
                    if (settings.validatorTypes[validatorType].validate($this, value, validator)) {
                      errorsFound.push(validator.message);
                    }
                  });
                }
              });

              return errorsFound;
            }
          );

          $this.bind(
            "getValidators.validation",
            function () {
              return validators;
            }
          );

          // =============================================================
          //                                             WATCH FOR CHANGES
          // =============================================================
          $this.bind(
            "submit.validation",
            function () {
              return $this.triggerHandler("change.validation", {submitting: true});
            }
          );
          $this.bind(
            [
              "keyup",
              "focus",
              "blur",
              "click",
              "keydown",
              "keypress",
              "change"
            ].join(".validation ") + ".validation",
            function (e, params) {

              var value = getValue($this);

              var errorsFound = [];

              $controlGroup.find("input,textarea,select").each(function (i, el) {
                var oldCount = errorsFound.length;
                $.each($(el).triggerHandler("validation.validation", params), function (j, message) {
                  errorsFound.push(message);
                });
                if (errorsFound.length > oldCount) {
                  $(el).attr("aria-invalid", "true");
                } else {
                  var original = $this.data("original-aria-invalid");
                  $(el).attr("aria-invalid", (original !== undefined ? original : false));
                }
              });

              $form.find("input,select,textarea").not($this).not("[name=\"" + $this.attr("name") + "\"]").trigger("validationLostFocus.validation");

              errorsFound = $.unique(errorsFound.sort());

              // Were there any errors?
              if (errorsFound.length) {
                // Better flag it up as a warning.
                $controlGroup.removeClass("success error").addClass("warning");

                // How many errors did we find?
                if (settings.options.semanticallyStrict && errorsFound.length === 1) {
                  // Only one? Being strict? Just output it.
                  $helpBlock.html(errorsFound[0] + 
                    ( settings.options.prependExistingHelpBlock ? $helpBlock.data("original-contents") : "" ));
                } else {
                  // Multiple? Being sloppy? Glue them together into an UL.
                  $helpBlock.html("<ul role=\"alert\"><li>" + errorsFound.join("</li><li>") + "</li></ul>" +
                    ( settings.options.prependExistingHelpBlock ? $helpBlock.data("original-contents") : "" ));
                }
              } else {
                $controlGroup.removeClass("warning error success");
                if (value.length > 0) {
                  $controlGroup.addClass("success");
                }
                $helpBlock.html($helpBlock.data("original-contents"));
              }

              if (e.type === "blur") {
                $controlGroup.removeClass("success");
              }
            }
          );
          $this.bind("validationLostFocus.validation", function () {
            $controlGroup.removeClass("success");
          });
        });
      },
      destroy : function( ) {

        return this.each(
          function() {

            var
              $this = $(this),
              $controlGroup = $this.parents(".form-group").first(),
              $helpBlock = $controlGroup.find(".help-block").first();

            // remove our events
            $this.unbind('.validation'); // events are namespaced.
            // reset help text
            $helpBlock.html($helpBlock.data("original-contents"));
            // reset classes
            $controlGroup.attr("class", $controlGroup.data("original-classes"));
            // reset aria
            $this.attr("aria-invalid", $this.data("original-aria-invalid"));
            // reset role
            $helpBlock.attr("role", $this.data("original-role"));
						// remove all elements we created
						if (createdElements.indexOf($helpBlock[0]) > -1) {
							$helpBlock.remove();
						}

          }
        );

      },
      collectErrors : function(includeEmpty) {

        var errorMessages = {};
        this.each(function (i, el) {
          var $el = $(el);
          var name = $el.attr("name");
          var errors = $el.triggerHandler("validation.validation", {includeEmpty: true});
          errorMessages[name] = $.extend(true, errors, errorMessages[name]);
        });

        $.each(errorMessages, function (i, el) {
          if (el.length === 0) {
            delete errorMessages[i];
          }
        });

        return errorMessages;

      },
      hasErrors: function() {

        var errorMessages = [];

        this.each(function (i, el) {
          errorMessages = errorMessages.concat(
            $(el).triggerHandler("getValidators.validation") ? $(el).triggerHandler("validation.validation", {submitting: true}) : []
          );
        });

        return (errorMessages.length > 0);
      },
      override : function (newDefaults) {
        defaults = $.extend(true, defaults, newDefaults);
      }
    },
		validatorTypes: {
      callback: {
        name: "callback",
        init: function ($this, name) {
          return {
            validatorName: name,
            callback: $this.data("validation" + name + "Callback"),
            lastValue: $this.val(),
            lastValid: true,
            lastFinished: true
          };
        },
        validate: function ($this, value, validator) {
          if (validator.lastValue === value && validator.lastFinished) {
            return !validator.lastValid;
          }

          if (validator.lastFinished === true)
          {
            validator.lastValue = value;
            validator.lastValid = true;
            validator.lastFinished = false;

            var rrjqbvValidator = validator;
            var rrjqbvThis = $this;
            executeFunctionByName(
              validator.callback,
              window,
              $this,
              value,
              function (data) {
                if (rrjqbvValidator.lastValue === data.value) {
                  rrjqbvValidator.lastValid = data.valid;
                  if (data.message) {
                    rrjqbvValidator.message = data.message;
                  }
                  rrjqbvValidator.lastFinished = true;
                  rrjqbvThis.data("validation" + rrjqbvValidator.validatorName + "Message", rrjqbvValidator.message);
                  // Timeout is set to avoid problems with the events being considered 'already fired'
                  setTimeout(function () {
                    rrjqbvThis.trigger("change.validation");
                  }, 1); // doesn't need a long timeout, just long enough for the event bubble to burst
                }
              }
            );
          }

          return false;

        }
      },
      ajax: {
        name: "ajax",
        init: function ($this, name) {
          return {
            validatorName: name,
            url: $this.data("validation" + name + "Ajax"),
            lastValue: $this.val(),
            lastValid: true,
            lastFinished: true
          };
        },
        validate: function ($this, value, validator) {
          if (""+validator.lastValue === ""+value && validator.lastFinished === true) {
            return validator.lastValid === false;
          }

          if (validator.lastFinished === true)
          {
            validator.lastValue = value;
            validator.lastValid = true;
            validator.lastFinished = false;
            $.ajax({
              url: validator.url,
              data: "value=" + value + "&field=" + $this.attr("name"),
              dataType: "json",
              success: function (data) {
                if (""+validator.lastValue === ""+data.value) {
                  validator.lastValid = !!(data.valid);
                  if (data.message) {
                    validator.message = data.message;
                  }
                  validator.lastFinished = true;
                  $this.data("validation" + validator.validatorName + "Message", validator.message);
                  // Timeout is set to avoid problems with the events being considered 'already fired'
                  setTimeout(function () {
                    $this.trigger("change.validation");
                  }, 1); // doesn't need a long timeout, just long enough for the event bubble to burst
                }
              },
              failure: function () {
                validator.lastValid = true;
                validator.message = "ajax call failed";
                validator.lastFinished = true;
                $this.data("validation" + validator.validatorName + "Message", validator.message);
                // Timeout is set to avoid problems with the events being considered 'already fired'
                setTimeout(function () {
                  $this.trigger("change.validation");
                }, 1); // doesn't need a long timeout, just long enough for the event bubble to burst
              }
            });
          }

          return false;

        }
      },
			regex: {
				name: "regex",
				init: function ($this, name) {
					return {regex: regexFromString($this.data("validation" + name + "Regex"))};
				},
				validate: function ($this, value, validator) {
					return (!validator.regex.test(value) && ! validator.negative)
						|| (validator.regex.test(value) && validator.negative);
				}
			},
			required: {
				name: "required",
				init: function ($this, name) {
					return {};
				},
				validate: function ($this, value, validator) {
					return !!(value.length === 0  && ! validator.negative)
						|| !!(value.length > 0 && validator.negative);
				},
        blockSubmit: true
			},
			match: {
				name: "match",
				init: function ($this, name) {
					var element = $this.parents("form").first().find("[name=\"" + $this.data("validation" + name + "Match") + "\"]").first();
					element.bind("validation.validation", function () {
						$this.trigger("change.validation", {submitting: true});
					});
					return {"element": element};
				},
				validate: function ($this, value, validator) {
					return (value !== validator.element.val() && ! validator.negative)
						|| (value === validator.element.val() && validator.negative);
				},
        blockSubmit: true
			},
			max: {
				name: "max",
				init: function ($this, name) {
					return {max: $this.data("validation" + name + "Max")};
				},
				validate: function ($this, value, validator) {
					return (parseFloat(value, 10) > parseFloat(validator.max, 10) && ! validator.negative)
						|| (parseFloat(value, 10) <= parseFloat(validator.max, 10) && validator.negative);
				}
			},
			min: {
				name: "min",
				init: function ($this, name) {
					return {min: $this.data("validation" + name + "Min")};
				},
				validate: function ($this, value, validator) {
					return (parseFloat(value) < parseFloat(validator.min) && ! validator.negative)
						|| (parseFloat(value) >= parseFloat(validator.min) && validator.negative);
				}
			},
			maxlength: {
				name: "maxlength",
				init: function ($this, name) {
					return {maxlength: $this.data("validation" + name + "Maxlength")};
				},
				validate: function ($this, value, validator) {
					return ((value.length > validator.maxlength) && ! validator.negative)
						|| ((value.length <= validator.maxlength) && validator.negative);
				}
			},
			minlength: {
				name: "minlength",
				init: function ($this, name) {
					return {minlength: $this.data("validation" + name + "Minlength")};
				},
				validate: function ($this, value, validator) {
					return ((value.length < validator.minlength) && ! validator.negative)
						|| ((value.length >= validator.minlength) && validator.negative);
				}
			},
			maxchecked: {
				name: "maxchecked",
				init: function ($this, name) {
					var elements = $this.parents("form").first().find("[name=\"" + $this.attr("name") + "\"]");
					elements.bind("click.validation", function () {
						$this.trigger("change.validation", {includeEmpty: true});
					});
					return {maxchecked: $this.data("validation" + name + "Maxchecked"), elements: elements};
				},
				validate: function ($this, value, validator) {
					return (validator.elements.filter(":checked").length > validator.maxchecked && ! validator.negative)
						|| (validator.elements.filter(":checked").length <= validator.maxchecked && validator.negative);
				},
        blockSubmit: true
			},
			minchecked: {
				name: "minchecked",
				init: function ($this, name) {
					var elements = $this.parents("form").first().find("[name=\"" + $this.attr("name") + "\"]");
					elements.bind("click.validation", function () {
						$this.trigger("change.validation", {includeEmpty: true});
					});
					return {minchecked: $this.data("validation" + name + "Minchecked"), elements: elements};
				},
				validate: function ($this, value, validator) {
					return (validator.elements.filter(":checked").length < validator.minchecked && ! validator.negative)
						|| (validator.elements.filter(":checked").length >= validator.minchecked && validator.negative);
				},
        blockSubmit: true
			}
		},
		builtInValidators: {
			email: {
				name: "Email",
				type: "shortcut",
				shortcut: "validemail"
			},
			validemail: {
				name: "Validemail",
				type: "regex",
				regex: "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\.[A-Za-z]{2,4}",
				message: "Not a valid email address<!-- data-validator-validemail-message to override -->"
			},
			passwordagain: {
				name: "Passwordagain",
				type: "match",
				match: "password",
				message: "Does not match the given password<!-- data-validator-paswordagain-message to override -->"
			},
			positive: {
				name: "Positive",
				type: "shortcut",
				shortcut: "number,positivenumber"
			},
			negative: {
				name: "Negative",
				type: "shortcut",
				shortcut: "number,negativenumber"
			},
			number: {
				name: "Number",
				type: "regex",
				regex: "([+-]?\\\d+(\\\.\\\d*)?([eE][+-]?[0-9]+)?)?",
				message: "Must be a number<!-- data-validator-number-message to override -->"
			},
			integer: {
				name: "Integer",
				type: "regex",
				regex: "[+-]?\\\d+",
				message: "No decimal places allowed<!-- data-validator-integer-message to override -->"
			},
			positivenumber: {
				name: "Positivenumber",
				type: "min",
				min: 0,
				message: "Must be a positive number<!-- data-validator-positivenumber-message to override -->"
			},
			negativenumber: {
				name: "Negativenumber",
				type: "max",
				max: 0,
				message: "Must be a negative number<!-- data-validator-negativenumber-message to override -->"
			},
			required: {
				name: "Required",
				type: "required",
				message: "This is required<!-- data-validator-required-message to override -->"
			},
			checkone: {
				name: "Checkone",
				type: "minchecked",
				minchecked: 1,
				message: "Check at least one option<!-- data-validation-checkone-message to override -->"
			}
		}
	};

	var formatValidatorName = function (name) {
		return name
			.toLowerCase()
			.replace(
				/(^|\s)([a-z])/g ,
				function(m,p1,p2) {
					return p1+p2.toUpperCase();
				}
			)
		;
	};

	var getValue = function ($this) {
		// Extract the value we're talking about
		var value = $this.val();
		var type = $this.attr("type");
		if (type === "checkbox") {
			value = ($this.is(":checked") ? value : "");
		}
		if (type === "radio") {
			value = ($('input[name="' + $this.attr("name") + '"]:checked').length > 0 ? value : "");
		}
		return value;
	};

  function regexFromString(inputstring) {
		return new RegExp("^" + inputstring + "$");
	}

  /**
   * Thanks to Jason Bunting via StackOverflow.com
   *
   * http://stackoverflow.com/questions/359788/how-to-execute-a-javascript-function-when-i-have-its-name-as-a-string#answer-359910
   * Short link: http://tinyurl.com/executeFunctionByName
  **/
  function executeFunctionByName(functionName, context /*, args*/) {
    var args = Array.prototype.slice.call(arguments).splice(2);
    var namespaces = functionName.split(".");
    var func = namespaces.pop();
    for(var i = 0; i < namespaces.length; i++) {
      context = context[namespaces[i]];
    }
    return context[func].apply(this, args);
  }

	$.fn.jqBootstrapValidation = function( method ) {

		if ( defaults.methods[method] ) {
			return defaults.methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
		} else if ( typeof method === 'object' || ! method ) {
			return defaults.methods.init.apply( this, arguments );
		} else {
		$.error( 'Method ' +  method + ' does not exist on jQuery.jqBootstrapValidation' );
			return null;
		}

	};

  $.jqBootstrapValidation = function (options) {
    $(":input").not("[type=image],[type=submit]").jqBootstrapValidation.apply(this,arguments);
  };

})( jQuery );

// Floating label headings for the contact form
$(function() {
    $("body").on("input propertychange", ".floating-label-form-group", function(e) {
        $(this).toggleClass("floating-label-form-group-with-value", !!$(e.target).val());
    }).on("focus", ".floating-label-form-group", function() {
        $(this).addClass("floating-label-form-group-with-focus");
    }).on("blur", ".floating-label-form-group", function() {
        $(this).removeClass("floating-label-form-group-with-focus");
    });
});

// Navigation Scripts to Show Header on Scroll-Up
jQuery(document).ready(function($) {
    var MQL = 1170;

    //primary navigation slide-in effect
    if ($(window).width() > MQL) {
        var headerHeight = $('.navbar-custom').height();
        $(window).on('scroll', {
                previousTop: 0
            },
            function() {
                var currentTop = $(window).scrollTop();
                //check if user is scrolling up
                if (currentTop < this.previousTop) {
                    //if scrolling up...
                    if (currentTop > 0 && $('.navbar-custom').hasClass('is-fixed')) {
                        $('.navbar-custom').addClass('is-visible');
                    } else {
                        $('.navbar-custom').removeClass('is-visible is-fixed');
                    }
                } else {
                    //if scrolling down...
                    $('.navbar-custom').removeClass('is-visible');
                    if (currentTop > headerHeight && !$('.navbar-custom').hasClass('is-fixed')) $('.navbar-custom').addClass('is-fixed');
                }
                this.previousTop = currentTop;
            });
    }
});

/*-------------------------------- */

function show_all_tweets(link,type){
   $("#loading_modal").modal("show");
   var value=$(link).attr("name");
   $.ajax({
          method: "GET",
          url: "/reload_tweets",
          dataType: "html",
          data: {value:value,polarity:type}
        })
          .done(function( data ) {
                var new_row=$(data);                
                //$("#row_2").html(new_row);                 
                $("#loading_modal").modal("hide"); 
                $("#modal_tweets") .html(new_row);
                $("#modal_tweets").modal("show");                
                return false;              
        });
 

};

$(".close").click(function(){
    $(this).parent().hide();
});


$("#tag_cloud .minimize_maximize").click(function(){
    $("#row_1").slideToggle(500);
    var img = $(this).find('img');
    if ($(img).attr("src")=='/static/img/maximize.png'){
        img.attr("src","/static/img/minimize.png");
        if($('#row_2').css('display') != 'none'){ 
                $('#tagCloudSmall').show();
                $('#pieChartSmall').show();
                $('#tagCloud').hide();
                $('#pieChart').hide();
                        
        }
        else{
                $('#tagCloudSmall').hide();
                $('#pieChartSmall').hide();
                $('#tagCloud').show();
                $('#pieChart').show();
        }
                
    }
    else
        img.attr("src","/static/img/maximize.png");
        
    return false;
  });
  
$("#tweets .minimize_maximize").click(function(){
    $("#row_2").slideToggle(500);
    var img = $(this).find('img');
    if ($(img).attr("src")=='/static/img/maximize.png'){
        img.attr("src","/static/img/minimize.png");
        if($('#row_1').css('display') != 'none'){ 
                $('#tagCloudSmall').show();
                $('#pieChartSmall').show();
                $('#tagCloud').hide();
                $('#pieChart').hide();
                        
        }
                
    }
    else{
        img.attr("src","/static/img/maximize.png");
        $('#tagCloudSmall').hide();
        $('#pieChartSmall').hide();
        $('#tagCloud').show();
        $('#pieChart').show();
    }
        
    return false;
  });
  
$("#orokorra1").parent().click(function(){
	$(".jarri").parent().attr("class","btn btn-lg btn-success active");
	$(".kendu").parent().attr("class","btn btn-lg btn-danger");
});

$("#orokorra2").parent().click(function(){
	
	$(".jarri").parent().attr("class","btn btn-lg btn-success");
	$(".kendu").parent().attr("class","btn btn-lg btn-danger active");
});

//$("#row_2").toggle();

$("input[name='options']").parent().click(function(){
    /*if ($(this).attr("class").indexOf("btn-success") >= 0){
        $("#denak1").parent().attr("class","btn btn-lg btn-success active");
        $("#denak2").parent().attr("class","btn btn-lg btn-danger");
    }*/
    $("input[name='options']").each(function(){
        var parent=$(this).parent();
        if ($(parent).hasClass("btn-danger"))
            $(parent).attr("class","btn btn-lg btn-danger");
        else
            $(parent).attr("class","btn btn-lg btn-success active");
    
    })
    refresh_from_buttons($(this));
    
    // Sartu hemen aldaketa kodea!
});

//Auto Refresh
var intervalID;
$("input[name='options0']").parent().click(function(){
    if ($(this).find("input").attr("id")=='option01'){
        intervalID=clearInterval(intervalID);
        intervalID="";
    }
    else{
        intervalID = setInterval(function(){auto_refresh();}, 900000);
    }
});

var word_cloud;

function show_pie(id,width,height){

        var canvasWidth=width;
        var canvasHeight=height;
        var pie = new d3pie(document.getElementById(id), {
	        
	        "size": {
		        "canvasWidth": canvasWidth,
                "canvasHeight": canvasHeight,
		        "pieOuterRadius": "65%"
	        },
	        "data": {
		        "sortOrder": "value-desc",
		        "content": [
			        {
				        "label": "Neutroak",
				        "value": neutroak,
				        "color": "#bfbfbf"
			        },
			        {
				        "label": "Positiboak",
				        "value": positiboak,
				        "color": "#56b510"
			        },
			        {
				        "label": "Negatiboak",
				        "value": negatiboak,
				        "color": "#ff4141"
			        }
		        ]
	        },
	        "labels": {
		        "outer": {
			        "pieDistance": 12
		        },
		        "inner": {
			        "hideWhenLessThanPercentage": 3
		        },
		        "mainLabel": {
			        "fontSize": 11
		        },
		        "percentage": {
			        "color": "#ffffff",
			        "decimalPlaces": 0
		        },
		        "value": {
			        "color": "#adadad",
			        "fontSize": 13
		        },
		        "lines": {
			        "enabled": true
		        },
		        "truncation": {
			        "enabled": true
		        }
	        },
	        "effects": {
		        "pullOutSegmentOnClick": {
			        "effect": "linear",
			        "speed": 400,
			        "size": 8
		        }
	        },
	        "misc": {
		        "gradient": {
			        "enabled": true,
			        "percentage": 100
		        }
	        }
        });


}



function show_tag_cloud(id,width,height){

    var wordInfo = JSON.parse(lainoa);
    //var wordInfo = JSON.parse('{"eljukebox":"11","dk_casares":"11","Donostiando":"12","BakeaPaz2016":"11","TrendsBeth":"10","keler":"10","suartezLC":"10","DSS2016":"25","cineffo":"11","2016_desokupatu":"11","Elhuyar":"11","Atekarri":"10","DonoSStiaoculta":"11","kabe_jrr":"11","sansebastianfes":"10","patxangas":"11","PetraZabalgana":"10","Emusik2016":"11","elcafederick":"11","sweetlittlehifi":"10","Andres_DiTella":"11","FomentoSS":"11","EgiaSegurua":"10","Imanol_Otaegi":"11","Ricardo_AMASTE":"11","imanolgallego":"10","cristina_enea":"11","donostiakultura":"14","ARQUIMANA":"10","AmagoiaLauzirik":"10","cineccdonostia":"11","kulturklik":"11","SSTurismo":"10","ereitenkz":"10","OlatuTalka":"14","donostia13":"10","egarate":"10","Feministaldia":"10","kutxakultur":"11","Donostilandia":"10","DavidJcome1":"12","AizpeaOM":"10","AATOMIC_LAB":"10","Elsekadero":"11","Zinea_eus":"11","MenofRockMusika":"10","foteropanico":"11","kutxakulturfest":"10","aquariumss":"10","paolaguimerans":"11","hirikilabs":"12","anderm68":"11","DSS2016Europe":"12","anestraat":"11","kortxoenea":"11","EUDialogues":"11","iortizgascon":"11","Carlos_Elorza":"11","Dricius":"11","filmotecavasca":"11","irutxulo":"11","fabusca":"12","jonpagola":"10","MirenMartin":"10","Poulidor77":"10","diariovasco":"10","joxeanurkiola":"10","xabipaya":"12","AsierBA85":"11","digilizar":"10","tabakalera":"17","MusicBox2016":"11","kulturaldia":"11","danilo_starz_":"10","interzonasinfo":"10","LaGuipuzcoana":"10","ARTEKLAB":"11","im_probables":"11","EnekoOlasagasti":"10","DJacomeNorato":"11","sonidoalpha":"12","Bihurgunea":"12","Bitorikova":"10","enekogoia":"11","AEGIkastetxea":"11","Amarapedia":"10","enarri":"10","garbibai":"10","djjacomenorato":"13","anerodriguez_a":"10","maiurbel":"10","raldarondo":"11","LaPublika":"10","GipuzkoadeModa":"11","DK_Liburutegiak":"11","Perutzio":"10","musiceoso":"10","e2020dss":"10","koldoartola":"10","ColaBoraBora":"11"}');

        var fill = d3.scale.category20();

        //var width = $('#tagCloud').parent().parent().width();

        var w = width;
        var h = height;

        word_cloud=d3.layout.cloud().size([w, h])
            .words(Object.keys(wordInfo).map(function(d){return {text:d, size: wordInfo[d]};}))
            .padding(1)	
        .timeInterval(400)
            .rotate(function() { return ~~(Math.random() * 2) * 0; })
            .font("Impact")
            .fontSize(function(d) { return d.size; })
            .on("end", draw)
            .start();

        function draw(words) {
              d3.select(id).append("svg")
                .attr("width", w) 
                .attr("height", h)
              .append("g")
                .attr("transform", "translate("+ [w >> 1, h >> 1] +")")
              .selectAll("text")
                .data(words)       
		.enter().append("text")
                //.style("font-size", function(d) { return d.size + "px"; })
	        .style("font-size", function(d) { return d.size + "px"; })
                //.style("font-size", function(d) { return Math.min( d.size,  d.size/this.getComputedTextLength() * 24) + "px"; })
		.style("font-family", "Impact")
	        .style("text-color", "black")
                .style("fill", function(d, i) { return fill(i); })
                .attr("text-anchor", "middle")
                .attr("transform", function(d) {
                    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
                })
                .text(function(d) { return d.text; })
                .on("click", function(d) {
                        reload_from_tag(d.text); }
                 ).on("mouseover", function(d) {
                        document.body.style.cursor = 'pointer'; }
                 )
                 .on("mouseout", function(d) {
                        document.body.style.cursor = 'default'; }
                 );
	 
            if ("author" == "author")
            {
	        //document.getElementById('tagCloud').style.display="none";
            }
        }

   /*
        function draw(words) {
              d3.select(id).append("svg")
                .attr("width", w) 
                .attr("height", h)
              .append("g")
                .attr("transform", "translate("+ [w >> 1, h >> 1] +")")
              .selectAll("text")
                .data(words)       
		.enter().append("text")
	        .attr("text-anchor", "middle")	        
		.each(function(d){
		    d3.select(this).append("tspan")
			.style("font-size", function(r) { return d.size + "px"; })
			.style("font-family", "Impact")
			.style("fill", "black")  //function(d, i) { return fill(i); })
			.attr("text-anchor", "middle")
			.attr("dy",0)
			.attr("x",0)
			.text(function(r) { return r.text; });
		    d3.select(this).append("tspan")
			.style("font-size", function(r) { return (d.size-5) + "px"; })
			.style("font-family", "Impact")
			.style("fill", "green") //.style("fill", function(d, i) { return fill(i); })
			.attr("text-anchor", "middle")
			.attr("dy",function(r){return (d.size*0.6) + "px";})
			.attr("x",0)
			.text(function(r) { return r.text; });
		    d3.select(this).append("tspan")
			.style("font-size", function(r) { return (d.size-5) + "px"; })
			.style("font-family", "Impact")
			.style("fill", "red")  //.style("fill", function(d, i) { return fill(i); })
			.attr("text-anchor", "middle")
			.attr("dy",function(r){return (d.size) + "px";})
			.attr("x",0)
			.text(function(r) { return r.text; });
		})
		.attr("transform", function(d) {
		    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";});

            if ("author" == "author")
            {
	        //document.getElementById('tagCloud').style.display="none";
            }
        }
*/
}


/* Hasieratu grafikoak */
show_tag_cloud('#tagCloud',$('#tagCloud').parent().parent().width(),$('#tagCloud').parent().parent().width()/1.7);
show_tag_cloud('#tagCloudSmall',$('#tagCloud').parent().parent().width(),$('#tagCloud').parent().parent().width()/3.8);
show_pie('pieChart',$('#pieChart').width(),$('#pieChart').width()*1.2);
show_pie('pieChartSmall',$('#pieChartSmall').width(),$('#pieChartSmall').width()/1.7);
$('#tagCloud').toggle();
$('#pieChart').toggle();


function reload_from_user(username){
    $("#loading_modal").modal("show");
    $.ajax({
          method: "GET",
          url: "/reload_page",
          dataType: "html",
          data: { username: username }
        })
          .done(function( data ) {
                var new_row=$(data)[0];
                neutroak = parseInt($(data)[2].innerHTML);
                positiboak = parseInt($(data)[4].innerHTML);
                negatiboak = parseInt($(data)[6].innerHTML);
                lainoa = $(data)[8].innerHTML;
                $("#row_2").html(new_row);                
                $('#pieChart svg').remove();
                $('#pieChartSmall svg').remove();
                $('#tagCloud svg').remove();
                $('#tagCloudSmall svg').remove();
                show_tag_cloud('#tagCloud',$('#tagCloud').parent().parent().width(),$('#tagCloud').parent().parent().width()/1.7);
                show_tag_cloud('#tagCloudSmall',$('#tagCloud').parent().parent().width(),$('#tagCloud').parent().parent().width()/3.8);
                show_pie('pieChart',$('#pieChart').width(),$('#pieChart').width()*1.2);
                show_pie('pieChartSmall',$('#pieChartSmall').width(),$('#pieChartSmall').width()/1.7);
                $("#tweets div h3 span").text(" (@"+username+")");
                $("#loading_modal").modal("hide");
        });

}
 

function reload_from_tag(tag_name){
    $("#loading_modal").modal("show");
    $.ajax({
          method: "GET",
          url: "/reload_page",
          dataType: "html",
          data: { tag_name: tag_name }
        })
          .done(function( data ) {
                var new_row=$(data)[0];
                neutroak = parseInt($(data)[2].innerHTML);
                positiboak = parseInt($(data)[4].innerHTML);
                negatiboak = parseInt($(data)[6].innerHTML);
                $("#row_2").html(new_row);                
                $('#pieChart svg').remove()
                $('#pieChartSmall svg').remove()
                show_pie('pieChart',$('#pieChart').width(),$('#pieChart').width()*1.2);
                show_pie('pieChartSmall',$('#pieChartSmall').width(),$('#pieChartSmall').width()/1.7);
                $("#tweets div h3 span").text(" (#"+tag_name+")");
                $("#loading_modal").modal("hide");
        });

}

function refresh_from_buttons(button){
    var id=$(button).find("input:first").attr("id");
    if (id.indexOf('1')==-1){
        // Botoia sakatu da
        reload_from_button(id.replace("2",""))
    }
    else{
        reload_all();
    }
}

function auto_refresh(){
    var inputs=$("input[name='options']");
    $(inputs).each(function(){
        if ($(this).parent().hasClass("btn-danger") && $(this).parent().hasClass("active"))
            id=$(this).attr('id');
    });
    if (id.indexOf('1')==-1){
        // Botoia sakatu da
        reload_from_button(id.replace("2",""))
    }
}


function reload_from_button(category){
    $("#loading_modal").modal("show");
    $.ajax({
          method: "GET",
          url: "/reload_page",
          dataType: "html",
          data: { category: category }
        })
          .done(function( data ) {
                var new_row=$(data)[0];
                neutroak = parseInt($(data)[2].innerHTML);
                positiboak = parseInt($(data)[4].innerHTML);
                negatiboak = parseInt($(data)[6].innerHTML);
                lainoa = $(data)[8].innerHTML;
                $("#row_2").html(new_row);
                $('#pieChart svg').remove();
                $('#pieChartSmall svg').remove();
                $('#tagCloud svg').remove();
                $('#tagCloudSmall svg').remove();
                show_pie('pieChart',$('#pieChart').width(),$('#pieChart').width()*1.2);
                show_pie('pieChartSmall',$('#pieChartSmall').width(),$('#pieChartSmall').width()/1.7);
                show_tag_cloud('#tagCloud',$('#tagCloud').parent().parent().width(),$('#tagCloud').parent().parent().width()/1.7);
show_tag_cloud('#tagCloudSmall',$('#tagCloud').parent().parent().width(),$('#tagCloud').parent().parent().width()/3.8);
                $("#tweets div h3 span").text(" ("+$("#"+category+"1").parent().text()+")");
                $("#loading_modal").modal("hide");
        });

}

function reload_all(){
    $(".jarri").parent().attr("class","btn btn-lg btn-success active");
    $(".kendu").parent().attr("class","btn btn-lg btn-danger");
    $("#loading_modal").modal("show");
    $.ajax({
          method: "GET",
          url: "/reload_page",
          dataType: "html",
          data: { category: 'all' }
        })
          .done(function( data ) {
                var new_row=$(data)[0];
                neutroak = parseInt($(data)[2].innerHTML);
                positiboak = parseInt($(data)[4].innerHTML);
                negatiboak = parseInt($(data)[6].innerHTML);
                lainoa = $(data)[8].innerHTML;
                $("#row_2").html(new_row);
                $('#pieChart svg').remove();
                $('#pieChartSmall svg').remove();
                $('#tagCloud svg').remove();
                $('#tagCloudSmall svg').remove();
                show_pie('pieChart',$('#pieChart').width(),$('#pieChart').width()*1.2);
                show_pie('pieChartSmall',$('#pieChartSmall').width(),$('#pieChartSmall').width()/1.7);
                show_tag_cloud('#tagCloud',$('#tagCloud').parent().parent().width(),$('#tagCloud').parent().parent().width()/1.7);
show_tag_cloud('#tagCloudSmall',$('#tagCloud').parent().parent().width(),$('#tagCloud').parent().parent().width()/3.8);
                var text=""
                $(".botoiak .active").each(function(){
                    if (text=='')
                        text=$(this).text();
                    else
                        text=text+" + "+$(this).text();
                });
                $("#tweets div h3 span").text("("+text+")");
                $(".show_more").attr("name","all");
                $("#loading_modal").modal("hide");
        });

}




     
