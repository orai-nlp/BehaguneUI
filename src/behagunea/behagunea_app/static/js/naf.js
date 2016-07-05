var Token = function(tokenElement) {
  this.element = tokenElement;
  this.id = tokenElement.data('id');
  this.sentence = parseInt(tokenElement.data('sentence'));
  this.paragraph = parseInt(tokenElement.data('paragraph'));
  this.length = parseInt(tokenElement.data('length'));
  this.offset = parseInt(tokenElement.data('offset'));
  this.simple_pos = tokenElement.data('spos');
  this.pos = tokenElement.data('pos');
  this.lemma = tokenElement.data('lemma');
  this.type = tokenElement.data('type');
  this.is_entity = tokenElement.data('entity') == 'True';
  this.entity_type = tokenElement.data('entity-type');
  this.word = tokenElement.text();
  this.popover = null;
  
  this.getPopoverContent = function() {
    var content = "<div>";
    content += "<div><strong>ID:&nbsp;</strong>" + this.id + "</div>";
    content += "<div><strong>Length: &nbsp;</strong>" + this.length + "</div>";
    content += "<div><strong>Sentence: &nbsp;</strong>" + this.sentence + "</div>";
    content += "<div><strong>Simple POS: &nbsp;</strong>" + this.simple_pos + "</div>";
    content += "<div><strong>Standard POS: &nbsp;</strong>" + this.pos + "</div>";
    content += "<div><strong>Lemma: &nbsp;</strong>" + this.lemma + "</div>";
    content += "<div><strong>Type: &nbsp;</strong>" + this.type + "</div>";
    if (this.is_entity) {
      content += "<div><strong>Entity Type: &nbsp;</strong>" + this.entity_type + "</div>";
    }
    content += "</div>";
    
    return content;
  }
  
  this.createPopover = function() {
    var word = this.word;
    var content = this.getPopoverContent();
    if (this.popover == null) {
      this.popover = this.element.popover({
        trigger: 'manual',
        placement: 'auto top',
        title: word,
        html: true,
        content: content
      });
    }
  }
}

var TokenInfoBoxes = function() {
  this.infoBoxes = {}
  this.currentlyDisplayedInfoBox = null;
  this.getInfoBox = function(token) {
    if (token.id in this.infoBoxes) {
      return this.infoBoxes[token.id];
    } else {
      var infoBox = new TokenInfoBox(token);
      this.infoBoxes[token.id] = infoBox;
      
      return infoBox;
    }
  }
  this.display = function(token) {
    var infoBox = this.getInfoBox(token);
    if (infoBox == this.currentlyDisplayedInfoBox) {
      infoBox.hide();
      this.currentlyDisplayedInfoBox = null;
    } else {
      if (this.currentlyDisplayedInfoBox != null) {
        this.currentlyDisplayedInfoBox.hide();
      }
      
      infoBox.display();
      this.currentlyDisplayedInfoBox = infoBox;
    }
  }
}

var TokenInfoBox = function(token) {
  this.token = token;
  this.display = function() {
    this.token.createPopover();
    var element = $(this.token.element);
    element.popover('show');
  }
  
  this.hide = function() {
    var element = $(this.token.element);
    element.popover('hide');
  }
}

var tokenInfoBoxes = new TokenInfoBoxes();

$(document).ready(function(){
  $('.tokens').on("click", '.token', function() {
    var token = new Token($(this));
    tokenInfoBoxes.display(token);
  });
});
