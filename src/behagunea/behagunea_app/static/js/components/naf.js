var tokens = window.tokens;

var Token = React.createClass({
  render: function() {
    var token = this.props.token;
    return (<span className='token'>{token.word}</span>);
  }
});

var Naf = React.createClass({
  render: function() {
    var tokens = this.props.tokens;
    return (
      <div className="naf">
        <h1>This is the naf visualization</h1>
        <div className="tokens">
        {tokens.map(token => <Token key={token.id} token={token} />)}
        </div>
      </div>
    );
  }
});

ReactDOM.render(
  <Naf tokens={tokens} />,
  document.getElementById('container')
);
