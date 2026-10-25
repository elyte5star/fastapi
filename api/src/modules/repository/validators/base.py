from pydantic import SecretStr, AfterValidator
import re
import uuid
from email_validator import validate_email, EmailNotValidError
from typing_extensions import Annotated
from fastapi.exceptions import RequestValidationError
from fastapi_mail.email_utils import DefaultChecker

# Password policy
SPECIAL_CHARS: set[str] = {
    "$",
    "@",
    "#",
    "%",
    "!",
    "^",
    "&",
    "*",
    "(",
    ")",
    "-",
    "_",
    "+",
    "=",
    "{",
    "}",
    "[",
    "]",
}


MIN_LENGTH: int = 5
MAX_LENGTH: int = 20
INCLUDES_SPECIAL_CHARS: bool = True
INCLUDES_NUMBERS: bool = True
INCLUDES_LOWERCASE: bool = True
INCLUDES_UPPERCASE: bool = True


def validate_password(v: SecretStr) -> SecretStr:
    min_length = MIN_LENGTH
    max_length = MAX_LENGTH
    includes_special_chars = INCLUDES_SPECIAL_CHARS
    includes_numbers = INCLUDES_NUMBERS
    includes_lowercase = INCLUDES_LOWERCASE
    includes_uppercase = INCLUDES_UPPERCASE
    special_chars = SPECIAL_CHARS

    if not isinstance(v.get_secret_value(), str):
        raise TypeError("string required")
    if len(v.get_secret_value()) < min_length or len(v.get_secret_value()) > max_length:
        raise RequestValidationError(
            f"length should be at least {min_length} but not more than 20"
        )

    if includes_numbers and not any(char.isdigit() for char in v.get_secret_value()):
        raise RequestValidationError("Password should have at least one numeral")

    if includes_uppercase and not any(char.isupper() for char in v.get_secret_value()):
        raise RequestValidationError("Password should have at least one uppercase letter")

    if includes_lowercase and not any(char.islower() for char in v.get_secret_value()):
        raise RequestValidationError("Password should have at least one lowercase letter")

    if includes_special_chars and not any(
        char in special_chars for char in v.get_secret_value()
    ):
        raise RequestValidationError(
            f"Password should have at least one of the symbols {special_chars}"
        )

    return v


ValidatePassword = Annotated[SecretStr, AfterValidator(validate_password)]


def username_validation(strParam: str) -> str:
    # username is between 4 and 25 characters
    if len(strParam) < 5 or len(strParam) > 20:
        raise RequestValidationError("length should be at least 5 but not more than 20")

    # start with a letter
    if not str(strParam[0]).isalpha():
        raise RequestValidationError("must start with letter")

    # can't end with an underscore
    if str(strParam[-1]) == "_":
        raise RequestValidationError("can't end with underscore")

    # contains only letters, numbers and underscore
    valid_grammar = set("abcdefghijklmnopqrstuvwxyz0123456789_")

    for ch in strParam:
        if ch.lower() not in valid_grammar:
            raise RequestValidationError(
                "Username can contain only letters,numbers and underscore"
            )
    return strParam


ValidateUsername = Annotated[str, AfterValidator(username_validation)]


def validate_mobile(value: str) -> str:
    rule = re.compile(
        r"^(?:(?:\(?(?:00|\+)([1-4]\d\d|[1-9]\d?)\)?)?[\-\.\ \\\/]?)?((?:\(?\d{1,}\)?[\-\.\ \\\/]?){0,})(?:[\-\.\ \\\/]?(?:#|ext\.?|extension|x)[\-\.\ \\\/]?(\d+))?$"
    )
    if len(value) > 20:
        raise RequestValidationError("length should not be more than 20")

    if not bool(rule.match(value)):
        RequestValidationError(f"{value} is an invalid mobile number")
    return value


ValidateTelephone = Annotated[str, AfterValidator(validate_mobile)]


def check_uuid(value: str) -> str:
    try:
        val = uuid.UUID(value, version=4)
        return str(val)
    except Exception:
        raise RequestValidationError(f"{value} is an invalid ID")


ValidateUUID = Annotated[str, AfterValidator(check_uuid)]


def is_valid_email(email: str) -> tuple[bool, str]:
    try:

        # Check that the email address is valid. Turn on check_deliverability
        # for first-time validations like on account creation pages (but not
        # login pages).
        emailinfo = validate_email(email, check_deliverability=False)

        # After this point, use only the normalized form of the email address,
        # especially before going to a database query.
        email = emailinfo.normalized
        return (True, email)
    except EmailNotValidError:
        return (False, email)


def email_validator(email: str) -> str:
    try:
        emailinfo = validate_email(email, check_deliverability=True)
        email = emailinfo.normalized
        return email
    except EmailNotValidError:
        raise RequestValidationError(f"{email} is an invalid/disposable email")


VerifyEmail = Annotated[str, AfterValidator(email_validator)]


async def default_checker():
    checker = DefaultChecker()  # you can pass source argument for your own email domains
    await checker.fetch_temp_email_domains()  # require to fetch temporary email domains
    return checker


countries = [
    {"text": "Afghanistan", "value": "AF"},
    {"text": "Åland Islands", "value": "AX"},
    {"text": "Albania", "value": "AL"},
    {"text": "Algeria", "value": "DZ"},
    {"text": "American Samoa", "value": "AS"},
    {"text": "Andorra", "value": "AD"},
    {"text": "Angola", "value": "AO"},
    {"text": "Anguilla", "value": "AI"},
    {"text": "Antarctica", "value": "AQ"},
    {"text": "Antigua and Barbuda", "value": "AG"},
    {"text": "Argentina", "value": "AR"},
    {"text": "Armenia", "value": "AM"},
    {"text": "Aruba", "value": "AW"},
    {"text": "Australia", "value": "AU"},
    {"text": "Austria", "value": "AT"},
    {"text": "Azerbaijan", "value": "AZ"},
    {"text": "Bahamas", "value": "BS"},
    {"text": "Bahrain", "value": "BH"},
    {"text": "Bangladesh", "value": "BD"},
    {"text": "Barbados", "value": "BB"},
    {"text": "Belarus", "value": "BY"},
    {"text": "Belgium", "value": "BE"},
    {"text": "Belize", "value": "BZ"},
    {"text": "Benin", "value": "BJ"},
    {"text": "Bermuda", "value": "BM"},
    {"text": "Bhutan", "value": "BT"},
    {"text": "Bolivia", "value": "BO"},
    {"text": "Bosnia and Herzegovina", "value": "BA"},
    {"text": "Botswana", "value": "BW"},
    {"text": "Bouvet Island", "value": "BV"},
    {"text": "Brazil", "value": "BR"},
    {"text": "British Indian Ocean Territory", "value": "IO"},
    {"text": "Brunei Darussalam", "value": "BN"},
    {"text": "Bulgaria", "value": "BG"},
    {"text": "Burkina Faso", "value": "BF"},
    {"text": "Burundi", "value": "BI"},
    {"text": "Cambodia", "value": "KH"},
    {"text": "Cameroon", "value": "CM"},
    {"text": "Canada", "value": "CA"},
    {"text": "Cape Verde", "value": "CV"},
    {"text": "Cayman Islands", "value": "KY"},
    {"text": "Central African Republic", "value": "CF"},
    {"text": "Chad", "value": "TD"},
    {"text": "Chile", "value": "CL"},
    {"text": "China", "value": "CN"},
    {"text": "Christmas Island", "value": "CX"},
    {"text": "Cocos (Keeling) Islands", "value": "CC"},
    {"text": "Colombia", "value": "CO"},
    {"text": "Comoros", "value": "KM"},
    {"text": "Congo", "value": "CG"},
    {"text": "Congo, The Democratic Republic of the", "value": "CD"},
    {"text": "Cook Islands", "value": "CK"},
    {"text": "Costa Rica", "value": "CR"},
    {"text": "Cote D'Ivoire", "value": "CI"},
    {"text": "Croatia", "value": "HR"},
    {"text": "Cuba", "value": "CU"},
    {"text": "Cyprus", "value": "CY"},
    {"text": "Czech Republic", "value": "CZ"},
    {"text": "Denmark", "value": "DK"},
    {"text": "Djibouti", "value": "DJ"},
    {"text": "Dominica", "value": "DM"},
    {"text": "Dominican Republic", "value": "DO"},
    {"text": "Ecuador", "value": "EC"},
    {"text": "Egypt", "value": "EG"},
    {"text": "El Salvador", "value": "SV"},
    {"text": "Equatorial Guinea", "value": "GQ"},
    {"text": "Eritrea", "value": "ER"},
    {"text": "Estonia", "value": "EE"},
    {"text": "Ethiopia", "value": "ET"},
    {"text": "Falkland Islands (Malvinas)", "value": "FK"},
    {"text": "Faroe Islands", "value": "FO"},
    {"text": "Fiji", "value": "FJ"},
    {"text": "Finland", "value": "FI"},
    {"text": "France", "value": "FR"},
    {"text": "French Guiana", "value": "GF"},
    {"text": "French Polynesia", "value": "PF"},
    {"text": "French Southern Territories", "value": "TF"},
    {"text": "Gabon", "value": "GA"},
    {"text": "Gambia", "value": "GM"},
    {"text": "Georgia", "value": "GE"},
    {"text": "Germany", "value": "DE"},
    {"text": "Ghana", "value": "GH"},
    {"text": "Gibraltar", "value": "GI"},
    {"text": "Greece", "value": "GR"},
    {"text": "Greenland", "value": "GL"},
    {"text": "Grenada", "value": "GD"},
    {"text": "Guadeloupe", "value": "GP"},
    {"text": "Guam", "value": "GU"},
    {"text": "Guatemala", "value": "GT"},
    {"text": "Guernsey", "value": "GG"},
    {"text": "Guinea", "value": "GN"},
    {"text": "Guinea-Bissau", "value": "GW"},
    {"text": "Guyana", "value": "GY"},
    {"text": "Haiti", "value": "HT"},
    {"text": "Heard Island and Mcdonald Islands", "value": "HM"},
    {"text": "Holy See (Vatican City State)", "value": "VA"},
    {"text": "Honduras", "value": "HN"},
    {"text": "Hong Kong", "value": "HK"},
    {"text": "Hungary", "value": "HU"},
    {"text": "Iceland", "value": "IS"},
    {"text": "India", "value": "IN"},
    {"text": "Indonesia", "value": "ID"},
    {"text": "Iran, Islamic Republic Of", "value": "IR"},
    {"text": "Iraq", "value": "IQ"},
    {"text": "Ireland", "value": "IE"},
    {"text": "Isle of Man", "value": "IM"},
    {"text": "Israel", "value": "IL"},
    {"text": "Italy", "value": "IT"},
    {"text": "Jamaica", "value": "JM"},
    {"text": "Japan", "value": "JP"},
    {"text": "Jersey", "value": "JE"},
    {"text": "Jordan", "value": "JO"},
    {"text": "Kazakhstan", "value": "KZ"},
    {"text": "Kenya", "value": "KE"},
    {"text": "Kiribati", "value": "KI"},
    {"text": "Korea, Democratic People'S Republic of", "value": "KP"},
    {"text": "Korea, Republic of", "value": "KR"},
    {"text": "Kuwait", "value": "KW"},
    {"text": "Kyrgyzstan", "value": "KG"},
    {"text": "Lao People'S Democratic Republic", "value": "LA"},
    {"text": "Latvia", "value": "LV"},
    {"text": "Lebanon", "value": "LB"},
    {"text": "Lesotho", "value": "LS"},
    {"text": "Liberia", "value": "LR"},
    {"text": "Libyan Arab Jamahiriya", "value": "LY"},
    {"text": "Liechtenstein", "value": "LI"},
    {"text": "Lithuania", "value": "LT"},
    {"text": "Luxembourg", "value": "LU"},
    {"text": "Macao", "value": "MO"},
    {"text": "Macedonia, The Former Yugoslav Republic of", "value": "MK"},
    {"text": "Madagascar", "value": "MG"},
    {"text": "Malawi", "value": "MW"},
    {"text": "Malaysia", "value": "MY"},
    {"text": "Maldives", "value": "MV"},
    {"text": "Mali", "value": "ML"},
    {"text": "Malta", "value": "MT"},
    {"text": "Marshall Islands", "value": "MH"},
    {"text": "Martinique", "value": "MQ"},
    {"text": "Mauritania", "value": "MR"},
    {"text": "Mauritius", "value": "MU"},
    {"text": "Mayotte", "value": "YT"},
    {"text": "Mexico", "value": "MX"},
    {"text": "Micronesia, Federated States of", "value": "FM"},
    {"text": "Moldova, Republic of", "value": "MD"},
    {"text": "Monaco", "value": "MC"},
    {"text": "Mongolia", "value": "MN"},
    {"text": "Montserrat", "value": "MS"},
    {"text": "Morocco", "value": "MA"},
    {"text": "Mozambique", "value": "MZ"},
    {"text": "Myanmar", "value": "MM"},
    {"text": "Namibia", "value": "NA"},
    {"text": "Nauru", "value": "NR"},
    {"text": "Nepal", "value": "NP"},
    {"text": "Netherlands", "value": "NL"},
    {"text": "Netherlands Antilles", "value": "AN"},
    {"text": "New Caledonia", "value": "NC"},
    {"text": "New Zealand", "value": "NZ"},
    {"text": "Nicaragua", "value": "NI"},
    {"text": "Niger", "value": "NE"},
    {"text": "Nigeria", "value": "NG"},
    {"text": "Niue", "value": "NU"},
    {"text": "Norfolk Island", "value": "NF"},
    {"text": "Northern Mariana Islands", "value": "MP"},
    {"text": "Norway", "value": "NO"},
    {"text": "Oman", "value": "OM"},
    {"text": "Pakistan", "value": "PK"},
    {"text": "Palau", "value": "PW"},
    {"text": "Palestinian Territory, Occupied", "value": "PS"},
    {"text": "Panama", "value": "PA"},
    {"text": "Papua New Guinea", "value": "PG"},
    {"text": "Paraguay", "value": "PY"},
    {"text": "Peru", "value": "PE"},
    {"text": "Philippines", "value": "PH"},
    {"text": "Pitcairn", "value": "PN"},
    {"text": "Poland", "value": "PL"},
    {"text": "Portugal", "value": "PT"},
    {"text": "Puerto Rico", "value": "PR"},
    {"text": "Qatar", "value": "QA"},
    {"text": "Reunion", "value": "RE"},
    {"text": "Romania", "value": "RO"},
    {"text": "Russian Federation", "value": "RU"},
    {"text": "RWANDA", "value": "RW"},
    {"text": "Saint Helena", "value": "SH"},
    {"text": "Saint Kitts and Nevis", "value": "KN"},
    {"text": "Saint Lucia", "value": "LC"},
    {"text": "Saint Pierre and Miquelon", "value": "PM"},
    {"text": "Saint Vincent and the Grenadines", "value": "VC"},
    {"text": "Samoa", "value": "WS"},
    {"text": "San Marino", "value": "SM"},
    {"text": "Sao Tome and Principe", "value": "ST"},
    {"text": "Saudi Arabia", "value": "SA"},
    {"text": "Senegal", "value": "SN"},
    {"text": "Serbia and Montenegro", "value": "CS"},
    {"text": "Seychelles", "value": "SC"},
    {"text": "Sierra Leone", "value": "SL"},
    {"text": "Singapore", "value": "SG"},
    {"text": "Slovakia", "value": "SK"},
    {"text": "Slovenia", "value": "SI"},
    {"text": "Solomon Islands", "value": "SB"},
    {"text": "Somalia", "value": "SO"},
    {"text": "South Africa", "value": "ZA"},
    {"text": "South Georgia and the South Sandwich Islands", "value": "GS"},
    {"text": "Spain", "value": "ES"},
    {"text": "Sri Lanka", "value": "LK"},
    {"text": "Sudan", "value": "SD"},
    {"text": "Suriname", "value": "SR"},
    {"text": "Svalbard and Jan Mayen", "value": "SJ"},
    {"text": "Swaziland", "value": "SZ"},
    {"text": "Sweden", "value": "SE"},
    {"text": "Switzerland", "value": "CH"},
    {"text": "Syrian Arab Republic", "value": "SY"},
    {"text": "Taiwan, Province of China", "value": "TW"},
    {"text": "Tajikistan", "value": "TJ"},
    {"text": "Tanzania, United Republic of", "value": "TZ"},
    {"text": "Thailand", "value": "TH"},
    {"text": "Timor-Leste", "value": "TL"},
    {"text": "Togo", "value": "TG"},
    {"text": "Tokelau", "value": "TK"},
    {"text": "Tonga", "value": "TO"},
    {"text": "Trinidad and Tobago", "value": "TT"},
    {"text": "Tunisia", "value": "TN"},
    {"text": "Turkey", "value": "TR"},
    {"text": "Turkmenistan", "value": "TM"},
    {"text": "Turks and Caicos Islands", "value": "TC"},
    {"text": "Tuvalu", "value": "TV"},
    {"text": "Uganda", "value": "UG"},
    {"text": "Ukraine", "value": "UA"},
    {"text": "United Arab Emirates", "value": "AE"},
    {"text": "United Kingdom", "value": "GB"},
    {"text": "United States", "value": "US"},
    {"text": "United States Minor Outlying Islands", "value": "UM"},
    {"text": "Uruguay", "value": "UY"},
    {"text": "Uzbekistan", "value": "UZ"},
    {"text": "Vanuatu", "value": "VU"},
    {"text": "Venezuela", "value": "VE"},
    {"text": "Viet Nam", "value": "VN"},
    {"text": "Virgin Islands, British", "value": "VG"},
    {"text": "Virgin Islands, U.S.", "value": "VI"},
    {"text": "Wallis and Futuna", "value": "WF"},
    {"text": "Western Sahara", "value": "EH"},
    {"text": "Yemen", "value": "YE"},
    {"text": "Zambia", "value": "ZM"},
    {"text": "Zimbabwe", "value": "ZW"},
]
