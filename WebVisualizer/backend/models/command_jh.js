'use strict';
const {
  Model
} = require('sequelize');
module.exports = (sequelize, DataTypes) => {
  class command_jh extends Model {
    /**
     * Helper method for defining associations.
     * This method is not a part of Sequelize lifecycle.
     * The `models/index` file will call this method automatically.
     */
    static associate(models) {
      // define association here
    }
  };
  command_jh.init({
    time: DataTypes.DATE,
    cmd_string: DataTypes.STRING,
    arg_string: DataTypes.STRING,
    is_finish: DataTypes.INTEGER,
  }, {
    sequelize,
    modelName: 'command_jh',
    tableName: 'command_jh'
  });
  return command_jh;
};