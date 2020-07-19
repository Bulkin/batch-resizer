import QtQuick 2.3
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Dialogs 1.2

ApplicationWindow {
    title: qsTr("Batch resizer")
    width: 1280
    height: 800
    visible: true

    FileDialog {
        id: fileChooserDialog
        title: qsTr("Please choose files for batch processing")
        selectExisting: true
        selectMultiple: true
        onAccepted: {
            imageMagickDispatcher.add(fileChooserDialog.fileUrls)
        }
    }
    DropArea {
        anchors.fill: parent
        id: dropArea;
        onEntered: {
            drag.accept (Qt.LinkAction);
        }
        onDropped: {
            imageMagickDispatcher.add(drop.urls)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        RowLayout {
            Layout.margins: 3
            Button {
                text: qsTr("Browse")
                onClicked: fileChooserDialog.open()
            }
            Label {
                text: qsTr("Output format")
            }
            TextField {
                Layout.fillWidth: true
                placeholderText: "%n -- file name"
                text: imageMagickDispatcher.outputFormat
                onEditingFinished: imageMagickDispatcher.setOutputFormat(text)
            }
        }

        RowLayout {
            Layout.margins: 3
            Label {
                text: qsTr("Scale value")
            }
            Slider {
                id: percentSlider
                value: imageMagickDispatcher.scale
                minimumValue: 0
                maximumValue: 100
                onValueChanged: imageMagickDispatcher.setScale(value)
            }
            TextField {
                text: percentSlider.value.toFixed(1)
                onEditingFinished: imageMagickDispatcher.setScale(parseFloat(text))
                validator: DoubleValidator { bottom: 0; top: 100; }
            }
        }
        
        TableView {
            Layout.margins: 3
            id: fileListView
            Layout.fillHeight: true
            Layout.fillWidth: true
            model: imageMagickDispatcher.images
            selectionMode: SelectionMode.ExtendedSelection
            headerVisible: false
            TableViewColumn {
                width: 24
                delegate: Rectangle {
                    anchors.fill: parent
                    color: fileListView.model[styleData.row].status === "Ok" ?
                               "green" : "red"
                    opacity: fileListView.model[styleData.row].status === "Waiting" ?
                                 0 : 1
                }
            }

            TableViewColumn {
                role: 'name'
                width: 400
            }
            TableViewColumn {
                role: 'output'
                width: 400
            }
            TableViewColumn {
                role: 'status'
                width: 400
            }
            Keys.onPressed: {
                if (event.key === Qt.Key_Delete) {
                    var idxList = []
                    fileListView.selection.forEach(function (idx) {idxList.push(idx)})
                    imageMagickDispatcher.remove(idxList)
                }
            }
        }
        RowLayout {
            Layout.margins: 3
            Button {
                text: qsTr("Run")
                onClicked: imageMagickDispatcher.run()
            }
            Button {
                text: qsTr("Reset")
                onClicked: imageMagickDispatcher.reset()
            }
            Button {
                text: qsTr("Clear")
                onClicked: imageMagickDispatcher.clear()
            }
            Item { opacity: 0; Layout.fillWidth: true }
            Button {
                text: qsTr("Close")
                onClicked: Qt.quit()
            }
        }
    }
}
