window.onload = function() {
    init()
};


async function init() {
    ln_tn = getCookie("ln_tn")


    if (ln_tn !== null) {
	const response = await fetch('http://localhost:8080/api/is-valid?id=' + ln_tn);

	if (!response.ok) {
	    throw new Error(`Response status: ${response.status}`);
	}

	const json = await response.json();

	console.log(json)

	isValid = json.IsPaid

	if (!isValid) {
	    ln_tn = null
	    document.cookie = "ln_tn="
	}
    }
    
    
    if (ln_tn !== null) {
	const response = await fetch('http://localhost:8080/api/is-paid?id=' + ln_tn);

	if (!response.ok) {
	    throw new Error(`Response status: ${response.status}`);
	}

	const json = await response.json();

	console.log(json)

	isPaid = json.IsPaid

	if (isPaid) {
	    paid()
	}
    }
}

function getCookie(name) {
    function escape(s) { return s.replace(/([.*+?\^$(){}|\[\]\/\\])/g, '\\$1'); }
    var match = document.cookie.match(RegExp('(?:^|;\\s*)' + escape(name) + '=([^;]*)'));
    return match ? match[1] : null;
}

function paid() {
    var divsToHide = document.getElementsByClassName("ad");
    for(var i = 0; i < divsToHide.length; i++){
        divsToHide[i].style.display = "none";
    }
    document.getElementById('sidebar').style.display = 'none';
    document.getElementById('payment').style.display = 'none';
}

async function ln_payment() {
    ln_tn = getCookie("ln_tn")

    if (ln_tn !== null && ln_tn != "") {
	window.open("https://checkout.dev.opennode.com/" + ln_tn, "_blank");
    } else {
	const response = await fetch('http://localhost:8080/api/create-payment');
	if (!response.ok) {
	    throw new Error(`Response status: ${response.status}`);
	}

	const json = await response.json();

	console.log(json)

	id = json.ID

	window.open("https://checkout.dev.opennode.com/" + json.ID, "_blank");
	document.cookie = "ln_tn=" + id
    }
}
