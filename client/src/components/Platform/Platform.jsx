import 'whatwg-fetch';
import React from 'react';
import { Icon, Image, Item, Label, Table, Container, Header, Button } from 'semantic-ui-react';
import PropTypes from 'prop-types';

class Platform extends React.Component {
  constructor(props) {
    super(props);
  }



  render() {
    const { platform, releases } = this.props;


    let releaseList = releases ? releases.map((release) => {

      const {download_url, name, size, sha} = release;
      console.log(release);

      const humanSize = (size / 1000000).toFixed(2);
      let install_dir='';
      let re = new RegExp(platform.releaseFormat);
      if (re.exec(name))
          install_dir='';
      else if (platform.additionalDataDir)
          install_dir=platform.additionalDataDir+'/';
      install_dir=install_dir+name;
         
      const install_url = '/api/download_url?dest='+install_dir+'&url='+download_url;
      return (
        <Table.Row>
          <Table.Cell>
            <Header as='h4'>
              <Header.Content>
                { name }
                <Header.Subheader>{ sha }</Header.Subheader>
              </Header.Content>
            </Header>
          </Table.Cell>
        <Table.Cell>
          <Button as="a" href={ download_url }>{`${humanSize}MB`}</Button>
        </Table.Cell>
        <Table.Cell>
          <Button as="a" href={ install_url }>Install</Button>
        </Table.Cell>
        </Table.Row>
      );
    }) : null;

    let imsrc ='';
    let link='';
    console.log(platform);
    if (platform)
    {
      if (platform.platformName &&  platform.type)
      {
           if (platform.type==='arcade')
           {
              imsrc =  '/static/images/HakchiMister/arcade/'+platform.platformName+'.png';
           }
           else
           {
              imsrc = '/static/images/HakchiMister/'+platform.platformName+'.png' ;
           }
      }
      if (platform.additionalDataDir)
         link='/files/filemanager?exclusiveFolder=/Cores/'+platform.additionalDataDir;
    }

    return platform ? (
      <Container>
        <Item.Group divided>
          <Item>
            <Item.Content>
              <Item.Header as="a"> { imsrc ? <Image size='medium' src={imsrc} verticalAlign="middle" /> : '' } { platform.name }</Item.Header>
              <Item.Meta>
                <span>{ platform.repo }</span>
              </Item.Meta>
              <Item.Description>{ platform.branch }</Item.Description>
              <Item.Extra>
                <Label>{ platform.type }</Label>
                <Label>{ platform.additionalData ? 'Additional Data Required' : 'No Additional Data Required'}</Label>
                { platform.additionalDataDir ? <Label as="a" href={link}><Icon name='folder'/> Browse {platform.additionalDataDir}</Label> : ""}
              </Item.Extra>
            </Item.Content>
          </Item>
        </Item.Group>
        <Table basic='very'>
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell>Release</Table.HeaderCell>
              <Table.HeaderCell>Download</Table.HeaderCell>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            { releaseList }
          </Table.Body>
        </Table>
      </Container>
    ) : null;
  }
}

Platform.propTypes = {
  platform: PropTypes.any.isRequired,
  releases: PropTypes.any.isRequired
};

export default Platform;
