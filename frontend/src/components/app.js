import React, { Component } from "react";
import { render } from "react-dom";
import {BrowserRouter as Router, Link, Route, Switch, Redirect } from "react-router-dom";

import Homepage from "../pages/Homepage";

export default class App extends Component {
    constructor(props) {
        super(props);
    }

    render() {
        return <Homepage />
    }
}

const appDiv = document.getElementById('app');

render(<App name='BonjourSanusi'/>, appDiv);