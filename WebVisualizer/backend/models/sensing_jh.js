'use strict';
const {
  Model
} = require('sequelize');
module.exports = (sequelize, DataTypes) => {
  class sensing_jh extends Model {
    /**
     * Helper method for defining associations.
     * This method is not a part of Sequelize lifecycle.
     * The `models/index` file will call this method automatically.
     */
    static associate(models) {
      // define association here
    }
  };
  sensing_jh.init({
    time: DataTypes.DATE,
    num1: DataTypes.DOUBLE,
    num2: DataTypes.DOUBLE,
    num3: DataTypes.DOUBLE,
    meta_string: DataTypes.STRING,
    is_finish: DataTypes.INTEGER,
  }, {
    sequelize,
    modelName: 'sensing_jh',
    tableName: 'sensing_jh',
  });
  return sensing_jh;
};