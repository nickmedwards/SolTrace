#pragma once

#include <QObject>
#include <QUrl>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>

class ScriptFSInterface : public QObject {
    Q_OBJECT
public:
    Q_INVOKABLE QJsonObject read(const QUrl &fileUrl) {
        QString fname = fileUrl.toLocalFile();
        QFile file(fname);
        if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) return QJsonObject();
        QJsonDocument itemDoc = QJsonDocument::fromJson(file.readAll());
        QJsonObject rootObject = itemDoc.object();
        return rootObject;
    }
};