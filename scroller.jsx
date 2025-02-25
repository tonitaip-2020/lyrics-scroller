var file = File.openDialog("Select your .csv file");  
if (file) {  
    file.open("r");  
    var comp = app.project.activeItem;  

    if (!(comp instanceof CompItem)) {  
        alert("Select a composition first!");  
    } else {  
        app.beginUndoGroup("Import Jumping Lyrics with 3-frame Yank");  
        
        var allLyrics = "";  
        var timings = [];  
        var lineHeight = 100; // Height of each line  

        while (!file.eof) {  
            var line = file.readln();  
            var data = line.split(",");  
            
            if (data.length >= 3) {  
                var startTime = parseTime(data[0]);  
                var text = data.slice(2).join(",").replace(/\"/g, ""); // Remove quotes  
                allLyrics += text + "\n";  
                timings.push({ time: startTime, index: timings.length });  
            }  
        }  

        file.close();  

        var totalLines = timings.length;
        var totalTextHeight = totalLines * lineHeight;  

        // Create a single text layer  
        var textLayer = comp.layers.addText(allLyrics);  
        var textProp = textLayer.property("Source Text");  
        var textDocument = textProp.value;  
        textDocument.fontSize = 80;  
        textDocument.fillColor = [1, 1, 1]; // White color  
        textDocument.justification = ParagraphJustification.CENTER_JUSTIFY;  
        textDocument.leading = lineHeight; // Set line height explicitly  
        textProp.setValue(textDocument);  

        // Get text layer dimensions correctly  
        var textBounds = textLayer.sourceRectAtTime(0, false);
        var textWidth = textBounds.width;
        var textHeight = textBounds.height;

        // Set the correct anchor point (center of text box)  
        textLayer.anchorPoint.setValue([textBounds.left + textWidth / 2, textBounds.top + textHeight / 2]);

        var pos = textLayer.property("Position");  
        var centerX = comp.width / 2;  

        // Calculate dynamic starting position for the first line  
        var firstLineY = (comp.height / 2) + (totalTextHeight / 2) - (lineHeight / 2);

        // Add "yank" motion keyframes with 3-frame spacing  
        for (var i = 0; i < timings.length; i++) {  
            var lineTime = timings[i].time;  
            var yOffset = firstLineY - (i * lineHeight);  // Move text UP as new lines are sung  

            // Keep position still until this line starts  
            if (i > 0) {  
                pos.setValueAtTime(lineTime, [centerX, yOffset]); // Hold position until the next line  
            }

            // Instant "yank" after the current line is sung  
            if (i < timings.length - 1) {  
                var nextLineTime = timings[i + 1].time;  
                pos.setValueAtTime(nextLineTime - 0.1, [centerX, yOffset]); // Hold for 3 frames (0.1s)  
                pos.setValueAtTime(nextLineTime, [centerX, yOffset + lineHeight]);  // Move up instantly  
            } else {  
                pos.setValueAtTime(lineTime, [centerX, yOffset]);  // Hold the last line's position  
            }
        }  

        app.endUndoGroup();  
    }  
}  

// Function to parse time (converting from string to number)  
function parseTime(timecode) {  
    return parseFloat(timecode) || 0; // Convert directly from decimal seconds  
}
